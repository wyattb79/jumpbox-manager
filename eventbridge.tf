resource "aws_cloudwatch_event_rule" "this" {
  name = "capture-ec2-creation"
  description = "Generate an event for any EC2 created"

  event_pattern = jsonencode({
    source = ["aws.ec2"]
    detail-type = ["EC2 Instance State-change Notification"]
    detail = {
      eventSource = ["ec2.amazonaws.com"]
      eventName = [""]
    }
  })
}
