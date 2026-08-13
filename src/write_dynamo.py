import json
import logging
import os
import boto3

REGION = os.environ.get('AWS_REGION')
DYNAMODB = boto3.resource('dynamodb', region_name=REGION)
TABLE_NAME = os.environ.get('TABLE_NAME', 'jumpbox_access')
TABLE = DYNAMODB.Table(TABLE_NAME)

LOGGER = logging.getLogger()
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "INFO").upper()
LOGGER.setLevel(LOG_LEVEL)


def handler(event, context):
  failed_message_ids = []

  for record in event.get('Records', []):
    message_id = record.get('messageId')
    try:
      LOGGER.info(f"Processing SQS message {message_id}")

      body_str = record.get('body', '{}')
      message_body = json.loads(body_str) if isinstance(body_str, str) else body_str

      instance_id = message_body.get('instance_id')
      remote_sg = message_body.get('remote_sg')
      jumpbox_sg = message_body.get('jumpbox_sg')

      if not instance_id or not remote_sg or not jumpbox_sg:
        LOGGER.warning(f"Message {message_id} is missing required fields. Skipping.")
        continue

      dynamo_row = {
        'InstanceId': instance_id,
        'remote_sg': remote_sg,
        'sg': jumpbox_sg
      }

      TABLE.put_item(Item=dynamo_row)
      LOGGER.info(f"Successfully wrote record for instance {instance_id} to DynamoDB")

    except Exception as err:
      LOGGER.error(f"Failed to write record {message_id} to DynamoDB: {err}", exc_info=True)
      if message_id:
        failed_message_ids.append(message_id)

    # Return partial batch failures so SQS can retry only failed items
    if failed_message_ids:
      return {
        "batchItemFailures": [
          {"itemIdentifier": msg_id} for msg_id in failed_message_ids
        ]
      }

    return {"statusCode": 200, "body": json.dumps("DynamoDB writes complete")}
