import json
import boto3
import logging
import os
from boto3.dynamodb.conditions import Key

region = os.environ.get('REGION')
ec2_client = boto3.client('ec2', region_name=region)

logger = logging.getLogger()
log_level = os.environ.get("LAMBDA_LOG_LEVEL", "INFO").upper()
logger.setLevel(logging.getLevelName(log_level))
queue_url = os.environ['SQS_QUEUE_URL']

def handler(event, context):

  for record in event['Records']:
    message_body = json.loads(record['body'])
    instance_id = message_body['detail']['instance-id']
    state = message_body['detail']['state']
    logger.info(f"Instance: {instance_id} now {state}")

    try:
      logger.info("Terminate")

      response = table.query(
        KeyConditionExpression=Key('InstanceId').eq(f"{instance_id}")
      )
      logger.info("Terminate2")
      Item = response.get('Items', [])
      logger.info(f"{Item}")
      logger.info(f"{response}")


    except Exception as e:
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
