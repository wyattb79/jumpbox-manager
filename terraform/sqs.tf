resource "aws_sqs_queue" "jumpbox_started" {
  name = "jumpbox-started"
  message_retention_seconds = 3600 

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.jumpbox-manager-created-dlq.arn
    maxReceiveCount = 5
  })
}

resource "aws_sqs_queue" "jumpbox_terminated" {
  name = "jumpbox-terminated"
  message_retention_seconds = 3600 

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.jumpbox-manager-terminated-dlq.arn
    maxReceiveCount = 5
  })
}

resource "aws_sqs_queue_policy" "allow_eventbridge_ec2create" {
  queue_url = aws_sqs_queue.jumpbox_started.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid = "AllowEventBridge"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action = "sqs:SendMessage"
      Resource = aws_sqs_queue.jumpbox_started.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_cloudwatch_event_rule.ec2_created.arn
        }
      }
    }]
  })
}

resource "aws_sqs_queue_policy" "allow_eventbridge_ec2terminate" {
  queue_url = aws_sqs_queue.jumpbox_terminated.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid = "AllowEventBridge"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action = "sqs:SendMessage"
      Resource = aws_sqs_queue.jumpbox_terminated.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_cloudwatch_event_rule.ec2_terminated.arn
        }
      }
    }]
  })
}

resource "aws_sqs_queue" "jumpbox-manager-created-dlq" {
  name = "jumpbox-manager-created-dlq"
  message_retention_seconds = 3600
}

resource "aws_sqs_queue" "jumpbox-manager-terminated-dlq" {
  name = "jumpbox-manager-terminated-dlq"
  message_retention_seconds = 3600
}
