variable "python_runtime" {
  type = string
  description = "python runtime version for lambda"
}

variable "jumpbox_tag" {
  type = string
  description = "ec2 tag key to determine the ec2 is an ephemeral jumpbox"
}
