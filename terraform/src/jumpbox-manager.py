import json
import boto3

def handler(event, context):
  ec2_client = boto3.client('ec2')

  for record in event['Records']:
    message_body = json.loads(record['body'])

    instance_id = message_body['detail']['instance-id']

    print(f"Checking instance: {instance_id}")

    try:
      print("1 debug")
      response = ec2_client.describe_instances(InstanceIds=[instance_id])

      print("2 debug")
      reservations = response.get('Reservations', [])

      print("3 debug")
      if not reservations:
        return "Instance not found"

      print("4 debug")
      instances = reservations[0].get('Instance', [])

      print("5 debug")
      if not instances:
        return "Instance not found"

      print("6 debug")
      tags = instances[0].get('Tags', [])
      print("7debug")
      jumpbox_tag = os.environ.get('JUMPBOX_TAG')
      print("8debug")
      label_key = next((tag['Key'] for tag in tags if tag['Key'] == jumpbox_tag), None)

      print("Found the tag")

      return {
        'statusCode': 200,
        'body': f'Found key {jumpbox_tag}'
      }

    except Exception as e:
      print("debug")
      return {
        'statusCode': 500,
        'body': f'Error fetching instance tags: {str(e)}'
      }

    print(f"Body content: {body}")

  return {
    'statusCode': 200,
    'body': json.dumps('Hello from Python')
  }
