import json
import boto3
import logging
import os

def handler(event, context):
  logger = logging.getLogger()
  log_level = os.environ.get("LAMBDA_LOG_LEVEL", "INFO").upper()
  logger.setLevel(logging.getLevelName(log_level))

  ec2_client = boto3.client('ec2', region_name='us-east-1')

  for record in event['Records']:
    message_body = json.loads(record['body'])
    instance_id = message_body['detail']['instance-id']
    logger.info(f"Checking instance: {instance_id}")

    try:
      logger.info("Attempting to grab SG")
      sg = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['SecurityGroups'][0]['GroupId']
      logger.info(f"The ID tht I discovered is {sg}")
      tags = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['Tags']
      resource_arn = next((tag['Value'] for tag in tags if tag['Key'] == 'Jumpbox_Resource'), None)
      remote_instance_id = resource_arn.split('/')[-1]
      logger.info(f"remote id is {remote_instance_id}")
      remote_sg = ec2_client.describe_instances(InstanceIds=[remote_instance_id])['Reservations'][0]['Instances'][0]['SecurityGroups'][0]['GroupId']
      logger.info(f"The remote ID tht I discovered is {remote_sg}")
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
      jumpbox_tag = os.environ.get('JUMPBOX_TAG')
      label_key = next((tag['Key'] for tag in tags if tag['Key'] == jumpbox_tag), None)
      logger.info("Ephemeral Jumpbox tag found")

      resource_arn = next((tag['Value'] for tag in tags if tag['Key'] == 'Jumpbox_Resource'), None)
      logger.info(f"Resource arn is {resource_arn}")

      return {
        'statusCode': 200,
        'body': f'Found key {jumpbox_tag}'
      }

    except Exception as e:
      error_code = e.response['Error']['Code']
      print(f"Error Code: {error_code}")
      error_message = e.response['Error']['Message']
      print(f"Reason: {error_message}")

      return {
        'statusCode': 500,
        'body': f'Error fetching instance tags: {str(e)}'
      }


  return {
    'statusCode': 200,
    'body': json.dumps('Hello from Python')
  }

