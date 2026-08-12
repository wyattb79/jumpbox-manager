module "ec2_started_queue" {
  source = "./modules/sqs-queue"
  queue_name = "ec2_started"
}

module "ec2_terminated_queue" {
  source = "./modules/sqs-queue"
  queue_name = "ec2_terminated"
}

module "read_dynamo_queue" {
  source = "./modules/sqs-queue"
  queue_name = "read_dynamo"
}

module "add_dynamo_queue" {
  source = "./modules/sqs-queue"
  queue_name = "add_dynamo"
}

module "delete_dynamo_queue" {
  source = "./modules/sqs-queue"
  queue_name = "delete_dynamo"
}

resource "aws_sqs_queue_policy" "allow_eventbridge_ec2create" {
  queue_url = module.ec2_started_queue.queue_id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid = "AllowEventBridge"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action = "sqs:SendMessage"
      Resource = module.ec2_started_queue.queue_arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = module.ec2_create_event.event_rule_arn
        }
      }
    }]
  })
}

resource "aws_sqs_queue_policy" "allow_eventbridge_ec2terminate" {
  queue_url = module.ec2_terminated_queue.queue_id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid = "AllowEventBridge"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action = "sqs:SendMessage"
      Resource = module.ec2_terminated_queue.queue_arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = module.ec2_terminate_event.event_rule_arn
        }
      }
    }]
  })
}

resource "aws_sqs_queue_policy" "allow_lambda_write_dynamo" {
  queue_url = module.add_dynamo_queue.queue_id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid = "AllowLambdaWrite"
      Effect = "Allow"
      Principal = {
      }
      Action = "sqs:SendMessage"
      Resource = module.add_dynamo_queue.queue_arn
    }]
  })
}
