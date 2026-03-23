variable "aws_region" {
  description = "AWS region for backend and resources. Override via TF_VAR_aws_region."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix for S3, Athena, and Glue resource names (must be globally unique for S3)."
  type        = string
  default     = "flights"
}

variable "environments" {
  description = "Logical environments to provision (each gets isolated buckets, Athena, Glue)."
  type        = list(string)
  default     = ["dev"]
}
