variable "aws_region" {
  description = "AWS region for backend and resources. Override via TF_VAR_aws_region."
  type        = string
  default     = "us-east-1"
}
