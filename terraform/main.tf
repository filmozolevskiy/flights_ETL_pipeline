locals {
  environments = toset(var.environments)
}

module "s3_data_lake" {
  source = "./modules/s3_data_lake"

  for_each = local.environments

  project_name = var.project_name
  environment  = each.key
}

module "athena_glue" {
  source = "./modules/athena_glue"

  for_each = local.environments

  project_name            = var.project_name
  environment             = each.key
  bronze_bucket_id        = module.s3_data_lake[each.key].bronze_bucket_id
  pipeline_logs_bucket_id = module.s3_data_lake[each.key].pipeline_logs_bucket_id
}
