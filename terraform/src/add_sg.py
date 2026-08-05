import json
import boto3
import logging
import os

region = os.environ.get('REGION')
ec2_client = boto3.client('ec2', region_name=region)

logger = logging.getLogger()
log_level = os.environ.get("LAMBDA_LOG_LEVEL", "INFO").upper()
logger.setLevel(logging.getLevelName(log_level))

def handler(event, context):

  for record in event['Records']:
    message_body = json.loads(record['body'])
    instance_id = message_body['detail']['instance-id']

    logger.info(f"Instance {instance_id} created")

    try:
      # get tagged instance and verify it exists
      tags = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['Tags']
 
      logger.info("1")
      # get the resource the jumpbox is requesting to access
      resource_arn = next((tag['Value'] for tag in tags if tag['Key'] == 'Jumpbox_Resource'), None)
  
      logger.info("2")
      if not resources_exist(resource_arn):
        return {
          'statusCode': 200,
          'body': f'Resource error.  Check your parameters to verify each resource exists'
        }
  
      logger.info("3")
      # get security group
      sg = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['SecurityGroups'][0]['GroupId']
  
      logger.info("4")
      remote_instance_id = resource_arn.split('/')[-1]
      logger.info("5")
      remote_sg = ec2_client.describe_instances(InstanceIds=[remote_instance_id])['Reservations'][0]['Instances'][0]['SecurityGroups'][0]['GroupId']
      logger.info("6")
  
      # verify that the newly started instance is a jumpbox
      jumpbox_tag = os.environ.get('JUMPBOX_TAG')
      logger.info("7")
      label_key = next((tag['Key'] for tag in tags if tag['Key'] == jumpbox_tag), None)
      logger.info("8")
  
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
      logger.info("SG Rule added")

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
    logger.info("a") 
    try:
      logger.info("b") 
      instance_id = ec2_arn.split(':')[5].split('/')[-1]
      logger.info("c") 
      response = ec2_client.describe_instances(InstanceIds=[instance_id])
      logger.info("d") 
    except Exception:
      logger.info("e") 
      return False
    return True
