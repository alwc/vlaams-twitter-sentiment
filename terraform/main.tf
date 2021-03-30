terraform {
  required_version = ">= 0.12.20"
  backend "s3" {
    workspace_key_prefix = "workspace"
    encrypt              = true
  }
}

# Providers

# The workspace account in which we will create (almost) all resources.
provider "aws" {
  region  = var.region
  version = "2.70.0"
}

# Alternate workspace account region necessary for https certificates only.
provider "aws" {
  alias   = "us_east_1"
  region  = "us-east-1"
  version = "2.70.0"
}

# Resources

# Package-specific resource name prefix.
locals {
  version_suffix    = terraform.workspace == "feature" ? "-${var.git_branch}" : ""
  version_slug      = "v${var.package_version}${local.version_suffix}"
  name_prefix       = "${terraform.workspace}-${var.package-slug}-${local.version_slug}"
  workspace_account = var.workspace_accounts[terraform.workspace]
}

# Domain name local variables.
locals {
  workspace_url_prefixes = {
    infrastructure = "inf."
    feature        = "ftr."
    development    = "dev."
    acceptance     = "uat."
    production     = ""
  }
  domain               = "sentiment-flanders.radix.sh"
  api_domain           = "api.${local.domain}"
  workspace_domain     = "${local.workspace_url_prefixes[terraform.workspace]}${local.domain}"
  workspace_api_domain = "${local.workspace_url_prefixes[terraform.workspace]}${local.api_domain}"
}

# Create a hosted zone for [ftr.][api.]sentiment-flanders.radix.sh.
#
# Important, you must create two NS records per workspace on the organisation account for the
# domains to work:
# - Hosted zone: radix.sh
# - NS record key: [ftr.][api.]sentiment-flanders.radix.sh.
# - NS record value: workspace account [ftr.][api.]sentiment-flanders.radix.sh nameservers
resource "aws_route53_zone" "workspace_domain" {
  name = local.workspace_domain
}
resource "aws_route53_zone" "workspace_api_domain" {
  name = local.workspace_api_domain
}

# Package-specific resources.

# Create a HTTPS certificate for [ftr.][api.]sentiment-flanders.radix.sh.
module "https_certificate" {
  source    = "./modules/https_certificate"
  providers = { aws = aws.us_east_1 }
  domains = [
    {
      domain  = local.workspace_domain
      zone_id = aws_route53_zone.workspace_domain.zone_id
    },
    {
      domain  = local.workspace_api_domain
      zone_id = aws_route53_zone.workspace_api_domain.zone_id
    }
  ]
}

# Create a CloudFront CDN that caches, compresses, and routes traffic to S3 or to Lambda.
module "cloudfront_cdn" {
  source            = "./modules/cloudfront_distribution"
  domain            = local.workspace_domain
  https_certificate = module.https_certificate.https_certificate
  hosted_zone       = aws_route53_zone.workspace_domain.zone_id
  origins = {
    "${module.s3_website_bucket.website_endpoint}" : {
      path_pattern : null,
      origin_type : "S3_WEBSITE",
      function_associations : []
    },
    "${local.workspace_api_domain}" : {
      path_pattern : "/api*",
      origin_type : "API_GATEWAY",
      function_associations : []
    }
  }
}

# Create an S3 website bucket to host the static assets.
module "s3_website_bucket" {
  source      = "./modules/s3_bucket"
  bucket_name = "${terraform.workspace}-${var.package-slug}-webapp"
  website     = true
}

# Create the serverless.yml file needed to deploy with Serverless.
module "serverless_yml" {
  source            = "./modules/serverless_yml"
  region            = var.region
  domain            = local.workspace_api_domain
  hosted_zone       = aws_route53_zone.workspace_api_domain.zone_id
  https_certificate = module.https_certificate.https_certificate
}

# Store runtime configuration for the Python package.
module "runtime_config" {
  source          = "./modules/runtime_config"
  package_name    = var.package-slug
  package_version = local.version_slug
  deploy          = jsondecode(var.deploy)
  config = {
    # Store variables you wish to access at runtime in this object.
  }
}

# Create AWS Batch job, this will run the following:
#  1. Create a compute environment (0..max_vcpus) with spot instances
#  2. Create job queue to place jobs on
#  3. Create job definition for jobs
#  4. Schedule the jobs on a given cron schedule
module "scheduled_batch_job" {
  source               = "./modules/scheduled_batch_job"
  name                 = "sentiment-flanders"
  max_vcpus            = 8
  schedule_expression  = "cron(0 2 * * ? *)" # 02:00 AM (UTC) every day (Belgium; 3AM Winter time / 4AM Summer time)
  container_properties = <<CONTAINER_PROPERTIES
{
    "command": ["update"],
    "image": "962194010810.dkr.ecr.eu-west-1.amazonaws.com/sentiment-flanders:latest",
    "memory": 4096,
    "vcpus": 8
}
CONTAINER_PROPERTIES
}
