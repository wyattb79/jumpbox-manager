import json
import boto3
import logging
import os
from boto3.dynamodb.conditions import Key

region = os.environ.get('REGION')
dynamodb = boto3.resource("dynamodb", region_name=region)
sqs_client = boto3.client('sqs')
TABLE_NAME = 'jumpbox_access'
table = dynamodb.Table(TABLE_NAME)

logger = logging.getLogger()
log_level = os.environ.get("LAMBDA_LOG_LEVEL", "INFO").upper()
logger.setLevel(logging.getLevelName(log_level))
queue_url = os.environ['SQS_QUEUE_URL']

def handler(event, context):

  for record in event['Records']:
    try:
      message_body = json.loads(record.get("body", {}))
      detail = message_body.get("detail", {})
      instance_id = detail.get("instance-id")
      state = detail.get("state")
  
      if not instance_id:
        logger.warning("No instance-id in record.  Skipping")
        continue
  
      logger.debug(f"Instance: {instance_id} now {state}")
  
      response = table.query(
        KeyConditionExpression=Key('InstanceId').eq(f"{instance_id}")
      )

      items = response.get('Items', [])

      if not items:
        logger.warning("No items found in Dynamo")
        continue

      item = items[0]
      remote_sg = item.get("remote_sg")
      jumpbox_sg = item.get("jumpbox_sg")

      message_data = {
        "instance_id": instance_id,
        "remote_sg": remote_sg,
        "jumpbox_sg": sg
      }

      response = sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody = json.dumps(message_data)
      )

    except Exception as e:
      return {
        'statusCode': 500,
        'body': ''
      }

  return {
    'statusCode': 200,
    'body': ''
  }
