output "athena_workgroup_name" {
  description = "Athena workgroup for Bronze exploration."
  value       = aws_athena_workgroup.exploration.name
}

output "glue_database_name" {
  description = "Glue catalog database for raw flights."
  value       = aws_glue_catalog_database.flights_raw.name
}

output "glue_table_name" {
  description = "Glue external table for bronze flights."
  value       = aws_glue_catalog_table.bronze_flights.name
}
