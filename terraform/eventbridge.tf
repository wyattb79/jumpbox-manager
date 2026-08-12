module "ec2_create_event" {
  source = "./modules/eventbridge-event"
  rule_name = "ec2-creation"
  rule_description = "Generate event for EC2 running"
  ec2_state = "running"
  queue_arn = module.ec2_started_queue.queue_arn
  target_id = "EC2-create" 
}

module "ec2_terminate_event" {
  source = "./modules/eventbridge-event"
  rule_name = "ec2-termination"
  rule_description = "Generate event for EC2 terminated"
  ec2_state = "terminated"
  queue_arn = module.read_dynamo_queue.queue_arn
  target_id = "EC2-terminate" 
}
