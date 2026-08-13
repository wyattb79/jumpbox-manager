import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get('AWS_REGION', os.environ.get('REGION'))
EC2_CLIENT = boto3.client('ec2', region_name=REGION)

LOGGER = logging.getLogger()
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "INFO").upper()
LOGGER.setLevel(LOG_LEVEL)


def handler(event, context):
    failed_message_ids = []

    for record in event.get('Records', []):
        message_id = record.get('messageId')
        try:
            body_str = record.get('body', '{}')
            message_body = json.loads(body_str) if isinstance(body_str, str) else body_str

            # ✅ Variable names fixed
            remote_sg = message_body.get('remote_sg')
            jumpbox_sg = message_body.get('jumpbox_sg')

            if not remote_sg or not jumpbox_sg:
                LOGGER.warning(f"Message {message_id} missing required security group IDs. Skipping.")
                continue

            # Revoke Security Group Ingress
            try:
                EC2_CLIENT.revoke_security_group_ingress(
                    GroupId=remote_sg,
                    IpPermissions=[{
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'UserIdGroupPairs': [{'GroupId': jumpbox_sg}]
                    }]
                )
                LOGGER.info(f"Successfully revoked ingress rule: {jumpbox_sg} -> {remote_sg}")
            except ClientError as e:
                # Handle idempotency: if already deleted, treat as success
                if e.response['Error']['Code'] == 'InvalidPermission.NotFound':
                    LOGGER.info(f"Ingress rule already revoked or non-existent: {jumpbox_sg} -> {remote_sg}")
                else:
                    raise

        except Exception as err:
            LOGGER.error(f"Failed to revoke rule for message {message_id}: {err}", exc_info=True)
            if message_id:
                failed_message_ids.append(message_id)

    # Return SQS standard batch failures
    return {
        "batchItemFailures": [
            {"itemIdentifier": msg_id} for msg_id in failed_message_ids
        ]
    }
