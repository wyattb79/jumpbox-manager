import json
import boto3
import logging
import os
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'jumpbox_access'
table = dynamodb.Table(TABLE_NAME)
region = os.environ.get('REGION')

def handler(event, context):
  logger = logging.getLogger()
  log_level = os.environ.get("LAMBDA_LOG_LEVEL", "INFO").upper()
  logger.setLevel(logging.getLevelName(log_level))

  ec2_client = boto3.client('ec2', region_name='us-east-1')

  for record in event['Records']:
    message_body = json.loads(record['body'])
    instance_id = message_body['detail']['instance-id']
    state = message_body['detail']['state']
    logger.info(f"Instance: {instance_id} now {state}")

    try:
      if state == "running":

        # get tagged instance and verify it exists
        tags = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['Tags']

        # get the resource the jumpbox is requesting to access
        resource_arn = next((tag['Value'] for tag in tags if tag['Key'] == 'Jumpbox_Resource'), None)
        logger.info("Checking exist")
        logger.info(f"Searching for {resource_arn}")
        if not resources_exist(resource_arn):
          return {
            'statusCode': 200,
            'body': f'Resource error.  Check your parameters to verify each resource exists'
          }
        logger.info("Exists")

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
        logger.info("Rule added")
        DynamoRow = {
          'InstanceId': remote_instance_id,
          'remote_sg': remote_sg,
          'sg': sg
        }
        table.put_item(Item=DynamoRow)
        logger.info("Record written to DynamoDB")

      elif state == "terminated":
        logger.info("Terminate")

        response = table.query(
          KeyConditionExpression=Key('InstanceId').eq(f"{instance_id}")
        )
        logger.info("Terminate2")
        Item = response.get('Items', [])
        logger.info(f"{Item}")
        logger.info(f"{response}")

        response = ec2_client.revoke_security_group_ingress(
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
        logger.info("Rule deleted")


    except Exception as e:
      error_code = e.response['Error']['Code']
      print(f"Error Code: {error_code}")
      error_message = e.response['Error']['Message']
      print(f"Reason: {error_message}")

      return {
        'statusCode': 500,
        'body': f'Error adding ingress rule: {str(e)}'
      }


  return {
    'statusCode': 200,
    'body': json.dumps('Rule added')
  }

def resources_exist(ec2_arn) -> bool:
  logger.info("Called func")
  try:
    logger.info("Tru1")
    instance_id = ec2_arn.split(':')[5].split('/')[-1]
    logger.info("Tru2")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    logger.info(response)
  except Exception:
    return False
  return True
