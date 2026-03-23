variable "project_name" {
  description = "Short project prefix for Athena workgroup and Glue database names."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, staging)."
  type        = string
}

variable "bronze_bucket_id" {
  description = "S3 bucket id for bronze raw JSON (Glue table location)."
  type        = string
}

variable "pipeline_logs_bucket_id" {
  description = "S3 bucket id for Athena query results and pipeline logs."
  type        = string
}
