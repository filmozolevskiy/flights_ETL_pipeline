resource "aws_athena_workgroup" "exploration" {
  name = "${var.project_name}-exploration-${var.environment}"

  configuration {
    enforce_workgroup_configuration    = false
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${var.pipeline_logs_bucket_id}/athena-results/"
    }
  }

  tags = {
    Purpose     = "bronze-exploration"
    Environment = var.environment
  }
}

resource "aws_glue_catalog_database" "flights_raw" {
  name        = "${var.project_name}_raw_${var.environment}"
  description = "Database for raw Bronze layer flight data (${var.environment})"
}

resource "aws_glue_catalog_table" "bronze_flights" {
  name          = "bronze_flights"
  database_name = aws_glue_catalog_database.flights_raw.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL = "TRUE"
  }

  partition_keys {
    name = "year"
    type = "string"
  }

  partition_keys {
    name = "month"
    type = "string"
  }

  partition_keys {
    name = "day"
    type = "string"
  }

  storage_descriptor {
    location      = "s3://${var.bronze_bucket_id}/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "openx-json"
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"

      parameters = {
        "ignore.malformed" = "true"
      }
    }

    columns {
      name = "status"
      type = "boolean"
    }

    columns {
      name = "message"
      type = "string"
    }

    columns {
      name = "api_timestamp"
      type = "string"
    }

    columns {
      name = "data"
      type = "string"
      comment = "Raw JSON data string (Task 3.2 will refine into structured schema)"
    }
  }
}
