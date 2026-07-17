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
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.this.arn
  function_name = aws_lambda_function.my_lambda.arn
  batch_size = 1
  enabled = true
}
