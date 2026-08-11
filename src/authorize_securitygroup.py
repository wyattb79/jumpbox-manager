import json
import boto3
import logging
import os

region = os.environ.get('REGION')
ec2_client = boto3.client('ec2', region_name=region)
sqs_client = boto3.client('sqs')
queue_url = os.environ['SQS_QUEUE_URL']

logger = logging.getLogger()
log_level = os.environ.get("LAMBDA_LOG_LEVEL", "INFO").upper()
logger.setLevel(logging.getLevelName(log_level))

def handler(event, context):

  for record in event['Records']:
    message_body = json.loads(record['body'])
    instance_id = message_body['detail']['instance-id']

    logger.info(f"Instance {instance_id} created")

    try:
      # get tagged instance and verify it exists
      tags = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['Tags']
 
      # get the resource the jumpbox is requesting to access
      resource_arn = next((tag['Value'] for tag in tags if tag['Key'] == 'Jumpbox_Resource'), None)
  
      if not resources_exist(resource_arn):
        return {
          'statusCode': 200,
          'body': f'Resource error.  Check your parameters to verify each resource exists'
        }
  
      # get security group
      sg = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['SecurityGroups'][0]['GroupId']
  
      remote_instance_id = resource_arn.split('/')[-1]
      remote_sg = ec2_client.describe_instances(InstanceIds=[remote_instance_id])['Reservations'][0]['Instances'][0]['SecurityGroups'][0]['GroupId']
  
      # verify that the newly started instance is a jumpbox
      jumpbox_tag = os.environ.get('JUMPBOX_TAG')
      label_key = next((tag['Key'] for tag in tags if tag['Key'] == jumpbox_tag), None)
  
      response = ec2_client.authorize_security_group_ingress(
        GroupId=remote_sg,  
        IpPermissions=[
          {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'UserIdGroupPairs': [
              {
                'GroupId': sg
              }
            ]
          }
        ]
      )
      logger.info("SG Rule added")

      message_data = {
        "instance_id": instance_id,
        "remote_sg": remote_sg,
        "jumpbox_sg": sg
      }

      response = sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody = json.dumps(message_data)
      )

      logger.info("Wrote to Queue")

    except Exception as e:
      error_type = type(e).__name__
      error_reason = str(e)

      logger.info(f"Type: {error_type} reason: {error_reason}")
      return {
               'statusCode': 500,
               'body': f'Error adding ingress rule: {str(e)}'
             }
  return {
    'statusCode': 200,
    'body': json.dumps('Rule added')
  }
  
def resources_exist(ec2_arn) -> bool:
  try:
    instance_id = ec2_arn.split(':')[5].split('/')[-1]
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
  except Exception:
    return False
  return True
