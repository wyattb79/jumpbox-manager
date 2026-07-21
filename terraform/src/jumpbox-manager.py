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
      logger.info("1 debug")
      response = ec2_client.describe_instances(InstanceIds=[instance_id])
      logger.info("{response}")
      logger.info("2 debug")
      reservations = response.get('Reservations', [])

      logger.info("3 debug")
      if not reservations:
        return "Instance not found"

      logger.info("4 debug")
      instances = reservations[0].get('Instance', [])

      logger.info("5 debug")
      if not instances:
        return "Instance not found"

      logger.info("6 debug")
      tags = instances[0].get('Tags', [])
      logger.info("7debug")
      jumpbox_tag = os.environ.get('JUMPBOX_TAG')
      logger.info("8debug")
      label_key = next((tag['Key'] for tag in tags if tag['Key'] == jumpbox_tag), None)

      logger.info("Found the tag")

      return {
        'statusCode': 200,
        'body': f'Found key {jumpbox_tag}'
      }

    except Exception as e:
      logger.info("debug")
      return {
        'statusCode': 500,
        'body': f'Error fetching instance tags: {str(e)}'
      }

    logger.info(f"Body content: {body}")

  return {
    'statusCode': 200,
    'body': json.dumps('Hello from Python')
  }
