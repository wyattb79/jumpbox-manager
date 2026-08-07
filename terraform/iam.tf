module "lambda_add_ingress_role" {
  source = "./modules/iam-role"
  role_name = "lambda_add_ingress"
  policy_arns = {
    "lamda_add_ingress" = aws_iam_policy.lambda_add_ingress_policy.arn 
  }
}

module "lambda_revoke_ingress_role" {
  source = "./modules/iam-role"
  role_name = "lambda_revoke_ingress"
  policy_arns = {
    "lambda_revoke_ingress" = aws_iam_policy.lambda_revoke_ingress_policy.arn
  }
}

module "lambda_add_dynamo_role" {
  source = "./modules/iam-role"
  role_name = "lambda_add_dynamo"
  policy_arns = {
    "lambda_add_dynamo" = aws_iam_policy.lambda_add_dynamo_policy.arn
  }
}

module "lambda_delete_dynamo_role" {
  source = "./modules/iam-role"
  role_name = "lambda_delete_dynamo"
  policy_arns = {
    "lambda_delete_dynamo" = aws_iam_policy.lambda_delete_dynamo_policy.arn
  }
}

resource "aws_iam_policy" "lambda_add_ingress_policy" {
  name = "lambda-add-ingress"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = [ module.ec2_started_queue.queue_arn ]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:AuthorizeSecurityGroupIngress",
        ]
        Resource = "arn:aws:ec2:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:security-group/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances"
        ]
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_policy" "lambda_revoke_ingress_policy" {
  name = "lambda-add-ingress"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = [ module.ec2_terminated_queue.queue_arn ]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:RevokeSecurityGroupIngress"
        ]
        Resource = "arn:aws:ec2:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:security-group/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances"
        ]
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_policy" "lambda_add_dynamo_policy" {
  name = "lambda-add-ingress"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = [ module.add_dynamo_queue.queue_arn ]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:Query",
        ]
        Resource: [ "arn:aws:dynamodb:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:table/jumpbox_access",
        "arn:aws:dynamodb:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:table/jumpbox_access/index/*"
        ]
      },
    ]
  })
}

resource "aws_iam_policy" "lambda_delete_dynamo_policy" {
  name = "lambda-add-ingress"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = [ module.delete_dynamo_queue.queue_arn ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:DeleteItem"
        ]
        Resource: [ "arn:aws:dynamodb:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:table/jumpbox_access",
        "arn:aws:dynamodb:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:table/jumpbox_access/index/*"
        ]
      },
    ]
  })
}
