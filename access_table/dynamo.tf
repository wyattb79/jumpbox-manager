resource "aws_dynamodb_table" "jumpbox_access" {
  name = "jumpbox_access"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "InstanceId"

  attribute {
    name = "InstanceId"
    type = "S"
  }
}
