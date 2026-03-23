output "bronze_bucket_id" {
  description = "Name (id) of the bronze raw data bucket."
  value       = aws_s3_bucket.bronze_raw.id
}

output "silver_bucket_id" {
  description = "Name (id) of the silver cleaned data bucket."
  value       = aws_s3_bucket.silver_cleaned.id
}

output "pipeline_logs_bucket_id" {
  description = "Name (id) of the pipeline logs bucket."
  value       = aws_s3_bucket.pipeline_logs.id
}
