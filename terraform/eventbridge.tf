resource "aws_cloudwatch_event_rule" "ec2_created" {
  name = "capture-ec2-creation"
  description = "Generate an event for any EC2 created"

  event_pattern = jsonencode({
    source = ["aws.ec2"]
    detail-type = ["EC2 Instance State-change Notification"]
    detail = {
      "state" = ["running"]
    }
  })
}

resource "aws_cloudwatch_event_target" "ec2_started" {
  rule = aws_cloudwatch_event_rule.ec2_created.name
  target_id = "send-to-sqs-started"
  arn = aws_sqs_queue.jumpbox_started.arn
}

resource "aws_cloudwatch_event_rule" "ec2_terminated" {
  name = "capture-ec2-termination"
  description = "Generate an event for any EC2 terminated"

  event_pattern = jsonencode({
    source = ["aws.ec2"]
    detail-type = ["EC2 Instance State-change Notification"]
    detail = {
      "state" = ["terminated"]
    }
  })
}

resource "aws_cloudwatch_event_target" "ec2_termianted" {
  rule = aws_cloudwatch_event_rule.ec2_terminated.name
  target_id = "send-to-sqs-terminated"
  arn = aws_sqs_queue.jumpbox_terminated.arn
}
