data "archive_file" "lambda_zip" {
  type = "zip"
  source_file = "${path.module}/src/jumpbox-manager.py"
  output_path = "${path.module}/src/jumpbox-manager.zip"
}

resource "aws_lambda_function" "my_lambda" {
  filename = data.archive_file.lambda_zip.output_path
  function_name = "jumpbox-manager"
  role = aws_iam_role.lambda_role.arn
  runtime = var.python_runtime
  handler = "jumpbox-manager.handler"

  environment {
    variables = {
      JUMPBOX_TAG = var.jumpbox_tag
    }
  }
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.this.arn
  function_name = aws_lambda_function.my_lambda.arn
  batch_size = 1
  enabled = true
}

resource "aws_subnet" "subnet_a" {
  vpc_id = var.vpc_id
  cidr_block = "10.0.1.0/24"
  availability_zone   = data.aws_availability_zones.available.names[0]
}

resource "aws_vpc_endpoint" "eks-ec2-endpoint" {
  vpc_id = var.vpc_id
  service_name = "com.amazonaws.us-east-1.ec2"
  vpc_endpoint_type = "Interface"
  private_dns_enabled = true

  subnet_ids = [
    aws_subnet.subnet_a.id
  ]

  security_group_ids = [
    aws_security_group.ec2_endpoint_sg.id
  ]
}


resource "aws_security_group" "lambda_sg" {
  name        = "lambda-sg"
  description = "Lambda security group"
  vpc_id      = var.vpc_id
}

resource "aws_vpc_security_group_egress_rule" "allow_lambda_outbound" {
  security_group_id = aws_security_group.lambda_sg.id
  ip_protocol = "-1"
  cidr_ipv4 = "0.0.0.0/0"
}

resource "aws_security_group" "ec2_endpoint_sg" {
  name        = "eks-ec2-endpoint-sg"
  description = "Security group that allows lambda to access ec2 endpoint"
  vpc_id      = var.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "allow_tls_lambda" {
  referenced_security_group_id = aws_security_group.lambda_sg.id
  security_group_id = aws_security_group.ec2_endpoint_sg.id
  description       = "Allow TLS to endpoint from lambda"

  ip_protocol = "-1"
}

data "aws_availability_zones" "available" {
  state = "available"
}
