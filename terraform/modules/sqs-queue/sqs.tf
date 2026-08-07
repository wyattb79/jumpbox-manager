resource "aws_sqs_queue" "this" {
  name = var.queue_name
  message_retention_seconds = 3600 

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.this_dlq.arn
    maxReceiveCount = 5
  })
}

resource "aws_sqs_queue" "this_dlq" {
  name = "${var.queue_name}-dlq"
  message_retention_seconds = 3600
}
