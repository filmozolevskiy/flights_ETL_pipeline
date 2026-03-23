resource "aws_s3_bucket" "bronze_raw" {
  bucket = "${var.project_name}-bronze-raw-${var.environment}"

  tags = {
    Layer       = "bronze"
    Purpose     = "raw-json"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "silver_cleaned" {
  bucket = "${var.project_name}-silver-cleaned-${var.environment}"

  tags = {
    Layer       = "silver"
    Purpose     = "cleaned-parquet"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "pipeline_logs" {
  bucket = "${var.project_name}-pipeline-logs-${var.environment}"

  tags = {
    Layer       = "logs"
    Purpose     = "pipeline-logs"
    Environment = var.environment
  }
}
