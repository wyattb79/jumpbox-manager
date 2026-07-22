import json
import boto3
import logging
import os

def handler(event, context):
  ec2_client = boto3.client('ec2', region_name='us-east-1')
  logger = logging.getLogger()

  log_level = os.environ.get("LAMBDA_LOG_LEVEL", "INFO").upper()
  logger.setLevel(logging.getLevelName(log_level))

  for record in event['Records']:
    message_body = json.loads(record['body'])

    instance_id = message_body['detail']['instance-id']

    logger.info(f"Checking instance: {instance_id}")

    try:
      response = ec2_client.describe_instances(InstanceIds=[instance_id])
      reservations = response.get('Reservations', [])

      if not reservations:
        return "Instance not found"

      instances = reservations[0].get('Instances', [])

      if not instances:
        return "Instance not found"

      tags = instances[0].get('Tags', [])
      jumpbox_tag = os.environ.get('JUMPBOX_TAG')
      label_key = next((tag['Key'] for tag in tags if tag['Key'] == jumpbox_tag), None)
      logger.info("Ephemeral Jumpbox tag found")

      sg_id = instances[0].get('SecurityGroups', [])    
      logger.info(f"Security group is: {sg_id}")

      return {
        'statusCode': 200,
        'body': f'Found key {jumpbox_tag}'
      }

    except Exception as e:
      return {
        'statusCode': 500,
        'body': f'Error fetching instance tags: {str(e)}'
      }


  return {
    'statusCode': 200,
    'body': json.dumps('Hello from Python')
  }
