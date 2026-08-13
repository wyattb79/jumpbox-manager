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

def handler(event, context):

  for record in event['Records']:
    message_body = json.loads(record['body'])
    remote_sg = message_body.get('remote_sg')
    jumpbox_sg = message_body.get('jumpbox_sg')

    try:
      response = ec2_client.revoke_security_group_ingress(
        GroupId=remote_sg,  
        IpPermissions=[
          {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'UserIdGroupPairs': [
              {
                'GroupId': jumpbox_sg
              }
            ]
          }
        ]
      )
      logger.info("Rule deleted")

    except Exception as e:
      return {
        'statusCode': 500,
        'body': f'Error adding ingress rule: {str(e)}'
      }


  return {
    'statusCode': 200,
    'body': json.dumps('Rule added')
  }
