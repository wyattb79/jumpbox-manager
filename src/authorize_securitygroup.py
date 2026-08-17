import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get('AWS_REGION')
EC2_CLIENT = boto3.client('ec2', region_name=REGION)
SQS_CLIENT = boto3.client('sqs', region_name=REGION)

QUEUE_URL = os.environ['SQS_QUEUE_URL']
JUMPBOX_TAG = os.environ.get('JUMPBOX_TAG', 'Jumpbox')

LOGGER = logging.getLogger()
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "INFO").upper()
LOGGER.setLevel(logging.getLevelName(LOG_LEVEL))

def handler(event, context):
  failed_message_ids = []

  for record in event.get('Records', []):
    message_id = record.get('messageId')
    try:
      body_str = record.get('body', '{}')
      message_body = json.loads(body_str) if isinstance(body_str, str) else body_str

      instance_id = message_body.get('detail', {}).get('instance-id')
      if not instance_id:
        LOGGER.warning(f"No instance-id in message {message_id}. Skipping.")
        continue

      LOGGER.info(f"Processing creation for instance: {instance_id}")

      # Fetch instance data once (tags + security groups)
      instance_data = get_instance_data(instance_id)
      if not instance_data:
        LOGGER.error(f"Instance {instance_id} not found or missing configuration.")
        continue

      tags = instance_data.get('Tags', [])
      security_groups = instance_data.get('SecurityGroups', [])

      if not security_groups:
        LOGGER.error(f"No security groups found for instance {instance_id}.")
        continue

      jumpbox_sg = security_groups[0].get('GroupId')
      if not jumpbox_sg:
        LOGGER.error(f"Security group missing GroupId key for instance {instance_id}.")
        continue
        
      # Validate jumpbox tag if required
      label_key = next((tag['Key'] for tag in tags if tag['Key'] == JUMPBOX_TAG), None)
      if not label_key:
        LOGGER.warning(f"Instance {instance_id} is missing required tag '{JUMPBOX_TAG}'. Skipping.")
        continue

      # Extract requested target resource ARN
      resource_arn = next((tag['Value'] for tag in tags if tag['Key'] == 'Jumpbox_Resource'), None)

      if not resource_arn or not resources_exist(resource_arn):
        LOGGER.warning(f"Resource check failed for ARN '{resource_arn}' on instance {instance_id}.")
        continue

      remote_instance_id = resource_arn.split('/')[-1]
      remote_data = get_instance_data(remote_instance_id)
      if not remote_data or not remote_data.get('SecurityGroups'):
        LOGGER.error(f"Remote instance {remote_instance_id} not found or missing security groups.")
        continue

      remote_sg = remote_sgs[0].get('GroupId')
      if not remote_sg:
        LOGGER.error(f"Remote security group missing GroupId key for instance {remote_instance_id}.")
        continue
        
      # Authorize Security Group Ingress (handling duplicate rule error gracefully)
      try:
        EC2_CLIENT.authorize_security_group_ingress(
          GroupId=remote_sg,
          IpPermissions=[
            {
              'IpProtocol': 'tcp',
              'FromPort': 22,
              'ToPort': 22,
              'UserIdGroupPairs': [{'GroupId': jumpbox_sg}]
            }
          ]
        )
        LOGGER.info(f"Ingress rule added: {jumpbox_sg} -> {remote_sg}")
      except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
          LOGGER.info(f"Ingress rule already exists: {jumpbox_sg} -> {remote_sg}")
        else:
          raise

      # Publish notification to downstream SQS queue
      message_data = {
        "instance_id": instance_id,
        "remote_sg": remote_sg,
        "jumpbox_sg": jumpbox_sg
      }

      SQS_CLIENT.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message_data)
      )
      LOGGER.info(f"Successfully queued update for instance {instance_id}")

    except Exception as err:
      LOGGER.error(f"Failed processing record {message_id}: {err}", exc_info=True)
      if message_id:
        failed_message_ids.append(message_id)

  return {
    "batchItemFailures": [
      {"itemIdentifier": msg_id} for msg_id in failed_message_ids
    ]
  }

def get_instance_data(instance_id: str) -> dict:
  """Helper to safely fetch instance details in a single EC2 call."""
  try:
    response = EC2_CLIENT.describe_instances(InstanceIds=[instance_id])
    reservations = response.get('Reservations', [])
    if reservations and reservations[0].get('Instances'):
      return reservations[0]['Instances'][0]
  except ClientError as e:
    LOGGER.error(f"EC2 describe_instances failed for {instance_id}: {e}")
  return {}


def resources_exist(ec2_arn: str) -> bool:
  """Safely checks if the resource target instance in the ARN exists."""
  if not isinstance(ec2_arn, str) or not ec2_arn:
    return False

  try:
    parts = ec2_arn.split(':')
    if len(parts) < 6:
      return False

    instance_id = parts[5].split('/')[-1]
    return bool(get_instance_data(instance_id))
  except Exception as e:
    LOGGER.warning(f"Error checking resource existence for {ec2_arn}: {e}")
    return False
