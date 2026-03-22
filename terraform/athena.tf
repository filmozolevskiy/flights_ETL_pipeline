# Athena workgroup and Glue catalog for Bronze data exploration

resource "aws_athena_workgroup" "exploration" {
  name = "flights-exploration"

  configuration {
    enforce_workgroup_configuration    = false
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.pipeline_logs.id}/athena-results/"
    }
  }

  tags = {
    Purpose = "bronze-exploration"
  }
}

resource "aws_glue_catalog_database" "flights_raw" {
  name        = "flights_raw"
  description = "Database for raw Bronze layer flight data"
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
    location      = "s3://${aws_s3_bucket.bronze_raw.id}/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "openx-json"
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"

      parameters = {
        "ignore.malformed"       = "true"
        "mapping.api_timestamp"   = "timestamp"
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
      name    = "data"
      type    = "struct<itineraries:struct<topFlights:array<struct<price:bigint,departure_time:string,arrival_time:string,stops:bigint,booking_token:string,airline_logo:string,self_transfer:boolean>>,otherFlights:array<struct<price:bigint,departure_time:string,arrival_time:string,stops:bigint,booking_token:string,airline_logo:string,self_transfer:boolean>>>>"
      comment = "Flight results; schema from API response (Task 3.2 will refine)"
    }
  }
}