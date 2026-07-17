resource "aws_cloudwatch_event_rule" "this" {
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

resource "aws_cloudwatch_event_target" "this" {
  rule = aws_cloudwatch_event_rule.this.name
  target_id = "send-to-sqs"
  arn = aws_sqs_queue.this.arn
}
