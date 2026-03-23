output "s3_buckets_by_environment" {
  description = "Bronze, silver, and pipeline log bucket names per environment."
  value = {
    for env, mod in module.s3_data_lake : env => {
      bronze = mod.bronze_bucket_id
      silver = mod.silver_bucket_id
      logs   = mod.pipeline_logs_bucket_id
    }
  }
}

output "athena_glue_by_environment" {
  description = "Athena workgroup and Glue identifiers per environment."
  value = {
    for env, mod in module.athena_glue : env => {
      athena_workgroup = mod.athena_workgroup_name
      glue_database    = mod.glue_database_name
      glue_table       = mod.glue_table_name
    }
  }
}
