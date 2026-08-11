import json
import boto3
import logging
import os

region = os.environ.get('REGION')
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'jumpbox_access'
table = dynamodb.Table(TABLE_NAME)

logger = logging.getLogger()
log_level = os.environ.get("LAMBDA_LOG_LEVEL", "INFO").upper()
logger.setLevel(logging.getLevelName(log_level))

def handler(event, context):

  for record in event['Records']:
    logger.info("Got message")
    message_body = json.loads(record['body'])
    instance_id = message_body['instance_id']
    remote_sg = message_body['remote_sg']
    jumpbox_sg = message_body['jumpbox_sg']

    try:
      DynamoRow = {
       'InstanceId': instance_id,
       'remote_sg': remote_sg,
       'sg': jumpbox_sg
      }
      table.put_item(Item=DynamoRow)
      logger.info("Record written to DynamoDB")

    except Exception as e:
      return {
        'statusCode': 500,
        'body': f'Error adding ingress rule: {str(e)}'
      }
  return {
    'statusCode': 200,
    'body': json.dumps('Rule added')
  }
