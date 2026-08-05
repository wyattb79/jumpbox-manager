data "archive_file" "add_sg_zip" {
  type = "zip"
  source_file = "${path.module}/src/add_sg.py"
  output_path = "${path.module}/src/add_sg.zip"
}

data "archive_file" "del_sg_zip" {
  type = "zip"
  source_file = "${path.module}/src/del_sg.py"
  output_path = "${path.module}/src/del_sg.zip"
}

resource "aws_lambda_function" "add_sg" {
  filename = data.archive_file.add_sg_zip.output_path
  function_name = "add_sg"
  role = aws_iam_role.lambda_role.arn
  runtime = var.python_runtime
  handler = "add_sg.handler"

  timeout = 30

  environment {
    variables = {
      JUMPBOX_TAG = var.jumpbox_tag,
      REGION = data.aws_region.current.name
    }
  }
}

resource "aws_lambda_event_source_mapping" "sqs_started_trigger" {
  event_source_arn = aws_sqs_queue.jumpbox_started.arn
  function_name = aws_lambda_function.add_sg.arn
  batch_size = 1
  enabled = true
}

resource "aws_lambda_function" "del_sg" {
  filename = data.archive_file.del_sg_zip.output_path
  function_name = "del_sg"
  role = aws_iam_role.lambda_role.arn
  runtime = var.python_runtime
  handler = "del_sg.handler"

  timeout = 30

  environment {
    variables = {
      JUMPBOX_TAG = var.jumpbox_tag,
      REGION = data.aws_region.current.name
    }
  }
}

resource "aws_lambda_event_source_mapping" "sqs_terminated_trigger" {
  event_source_arn = aws_sqs_queue.jumpbox_terminated.arn
  function_name = aws_lambda_function.del_sg.arn
  batch_size = 1
  enabled = true
}

