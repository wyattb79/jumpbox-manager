resource "aws_sqs_queue" "this" {
  name = "jumpbox-started"
  message_retention_seconds = 3600 

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.jumpbox-manager-dlq.arn
    maxReceiveCount = 5
  })
}

resource "aws_sqs_queue_policy" "allow_eventbridge" {
  queue_url = aws_sqs_queue.this.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid = "AllowEventBridge"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action = "sqs:SendMessage"
      Resource = aws_sqs_queue.this.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_cloudwatch_event_rule.this.arn
        }
      }
    }]
  })
}

resource "aws_sqs_queue" "jumpbox-manager-dlq" {
  name = "jumpbox-manager-dlq"
  message_retention_seconds = 3600
}

