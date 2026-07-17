import json

def handler(event, context):
  for record in event['Records']:
    message_id = record['messageId']
    body = record['body']

  return {
    'statusCode': 200,
    'body': json.dumps('Hello from Python')
  }
