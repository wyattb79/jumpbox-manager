import json
import logging
import os
import boto3
from boto3.dynamodb.conditions import Key

# Initialize AWS SDK clients outside the handler to reuse TCP connections
REGION = os.environ.get('AWS_REGION')
DYNAMODB = boto3.resource('dynamodb', region_name=REGION)
SQS_CLIENT = boto3.client('sqs', region_name=REGION)

TABLE_NAME = os.environ.get('TABLE_NAME', 'jumpbox_access')
QUEUE_URL = os.environ['SQS_QUEUE_URL']
TABLE = DYNAMODB.Table(TABLE_NAME)

# Set up logger
LOGGER = logging.getLogger()
LOG_LEVEL = os.environ.get('LAMBDA_LOG_LEVEL', 'INFO').upper()
LOGGER.setLevel(LOG_LEVEL)

def handler(event, context):
  failed_message_ids = []

  for record in event.get('Records', []):
    message_id = record.get('messageId')
    try:
      # SQS Record body is a string; handle potential JSON parsing issues
      body_str = record.get('body', '{}')
      message_body = json.loads(body_str) if isinstance(body_str, str) else body_str

      detail = message_body.get('detail', {})
      instance_id = detail.get('instance-id')
      state = detail.get('state')

      if not instance_id:
        LOGGER.warning(f"No instance-id found in record {message_id}. Skipping.")
        continue

      LOGGER.debug(f"Instance: {instance_id} state updated to: {state}")

      # Query DynamoDB for matching records
      response = TABLE.query(
        KeyConditionExpression=Key('InstanceId').eq(instance_id)
      )
      items = response.get('Items', [])

      if not items:
        LOGGER.warning(f"No DynamoDB items found for InstanceId: {instance_id}")
        continue

      item = items[0]
      message_data = {
        "instance_id": instance_id,
        "remote_sg": item.get("remote_sg"),
        "jumpbox_sg": item.get("jumpbox_sg")
      }

      # Forward structured message to target SQS Queue
      SQS_CLIENT.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message_data)
      )

    except Exception as err:
      LOGGER.error(f"Failed processing record {message_id}: {err}", exc_info=True)
      if message_id:
        failed_message_ids.append(message_id)

  # If processing SQS events in Lambda, return partial batch failures to avoid retrying successful items
  if failed_message_ids:
    return {
      "batchItemFailures": [
        {"itemIdentifier": msg_id} for msg_id in failed_message_ids
      ]
    }

    return {"statusCode": 200, "body": json.dumps("Processing complete")}
