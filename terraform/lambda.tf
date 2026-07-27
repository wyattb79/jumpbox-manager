data "archive_file" "jumpbox_manager_zip" {
  type = "zip"
  source_file = "${path.module}/src/jumpbox_manager.py"
  output_path = "${path.module}/src/jumpbox_manager.zip"
}

resource "aws_lambda_function" "jumpbox_manager" {
  filename = data.archive_file.jumpbox_manager_zip.output_path
  function_name = "jumpbox_manager"
  role = aws_iam_role.lambda_role.arn
  runtime = var.python_runtime
  handler = "jumpbox_manager.handler"

  timeout = 30

  environment {
    variables = {
      JUMPBOX_TAG = var.jumpbox_tag
    }
  }
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.this.arn
  function_name = aws_lambda_function.jumpbox_manager.arn
  batch_size = 1
  enabled = true
}

