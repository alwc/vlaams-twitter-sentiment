/*

# Purpose

Create this application's rendered `serverless.yml`.

# Usage

module "serverless_yml" {
  source = "./modules/serverless_yml"
  region = var.region
  domain = local.workspace_api_domain
  hosted_zone = aws_route53_zone.api.zone_id
  https_certificate = module.https_certificate.https_certificate
}

*/

resource "local_file" "serverless_yml" {
  content = templatefile("./modules/serverless_yml/serverless.tpl.yml", {
    workspace         = terraform.workspace
    region            = var.region
    domain            = var.domain
    https_certificate = var.https_certificate
    hosted_zone       = var.hosted_zone
  })
  filename = "${path.cwd}/../src/serverless.yml"
}
