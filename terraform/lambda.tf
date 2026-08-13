module "lambda_authorize_securitygroup" {
  source = "./modules/lambda-function"
  function_name = "authorize_securitygroup"
  role = module.lambda_add_ingress_role.role_arn
  region = data.aws_region.current.region
  python_runtime = var.python_runtime

  lambda_env_vars = {
    JUMPBOX_TAG = var.jumpbox_tag,
    REGION = data.aws_region.current.region
    SQS_QUEUE_URL = module.add_dynamo_queue.queue_id
  }

  queue_arn = module.ec2_started_queue.queue_arn
}

module "lambda_revoke_securitygroup" {
  source = "./modules/lambda-function"
  function_name = "revoke_securitygroup"
  role = module.lambda_revoke_ingress_role.role_arn
  region = data.aws_region.current.region
  python_runtime = var.python_runtime

  lambda_env_vars = {
    JUMPBOX_TAG = var.jumpbox_tag,
    REGION = data.aws_region.current.region
    SQS_QUEUE_URL = module.delete_dynamo_queue.queue_id
  }

  queue_arn = module.read_dynamo_queue.queue_arn
}

module "lambda_read_dynamo" {
  source = "./modules/lambda-function"
  function_name = "read_dynamo"
  role = module.lambda_read_dynamo_role.role_arn
  region = data.aws_region.current.region
  python_runtime = var.python_runtime

  lambda_env_vars = {
    REGION = data.aws_region.current.region
    SQS_QUEUE_URL = module.read_dynamo_queue.queue_id
  }

  queue_arn = module.ec2_started_queue.queue_arn
}

module "lambda_write_dynamo" {
  source = "./modules/lambda-function"
  function_name = "write_dynamo"
  role = module.lambda_add_dynamo_role.role_arn
  region = data.aws_region.current.region
  python_runtime = var.python_runtime

  queue_arn = module.add_dynamo_queue.queue_arn
}

module "lambda_delete_dynamo" {
  source = "./modules/lambda-function"
  function_name = "delete_dynamo"
  role = module.lambda_delete_dynamo_role.role_arn
  region = data.aws_region.current.region
  python_runtime = var.python_runtime

  queue_arn = module.delete_dynamo_queue.queue_arn
}

