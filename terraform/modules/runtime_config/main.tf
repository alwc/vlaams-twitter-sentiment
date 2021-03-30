/*

# Purpose

Create this application's runtime config.

# Usage

module "runtime_config" {
  source          = "./modules/runtime_config"
  package_name    = var.package-slug
  package_version = local.version_slug
  deploy          = jsondecode(var.deploy)
  config = {
    a = "b"
    c = {
      d = "e"
    }
  }
}

*/

locals {
  outputs = jsonencode(merge(var.deploy, var.config))
}

# The runtime config is read by the package's config module if it is available on disk.
resource "local_file" "terraform_outputs_json" {
  content  = local.outputs
  filename = "${path.cwd}/../src/sentiment_flanders/config/terraform.outputs.json"
}

# Else, the runtime config is fetched from the Parameter Store.
resource "aws_ssm_parameter" "parameter" {
  for_each    = toset([var.package_version, "latest"])
  name        = "/${terraform.workspace}/${var.package_name}/${each.key}"
  description = "The runtime config of the sentiment_flanders package"
  overwrite   = true
  tier        = var.tier
  type        = var.type
  value       = local.outputs
  # TODO: Add `abandon_on_destroy = true` [1] once implemented.
  # [1] https://github.com/hashicorp/terraform/issues/15485
}
