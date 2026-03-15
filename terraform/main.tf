# Core S3 buckets for the flights data lakehouse

resource "aws_s3_bucket" "bronze_raw" {
  bucket = "flights-bronze-raw"

  tags = {
    Layer   = "bronze"
    Purpose = "raw-json"
  }
}

resource "aws_s3_bucket" "silver_cleaned" {
  bucket = "flights-silver-cleaned"

  tags = {
    Layer   = "silver"
    Purpose = "cleaned-parquet"
  }
}

resource "aws_s3_bucket" "pipeline_logs" {
  bucket = "flights-pipeline-logs"

  tags = {
    Layer   = "logs"
    Purpose = "pipeline-logs"
  }
}
