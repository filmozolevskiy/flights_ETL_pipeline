variable "project_name" {
  description = "Short project prefix for globally unique S3 bucket names."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, staging)."
  type        = string
}
