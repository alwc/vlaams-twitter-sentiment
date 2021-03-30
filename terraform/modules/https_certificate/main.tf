/*

# Purpose

Create a verified HTTPS certificate [1] in the us-east-1 region for a list of
domains.

Note: you must foresee a provider in the us-east-1 region to host the https
certificate.

# Usage

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

module "https_certificate" {
  source  = "./modules/https_certificate"
  providers = { aws = aws.us_east_1 }
  domains = [
    {domain = "dev.example.com", zone_id = "Z1NIDS8WH5H399"},
    {domain = "dev.api.example.com", zone_id = "Z2NIDS8WH5H399"}
  ]
}

cert = "${module.https_certificate.https_certificate}"

# References

[1] https://www.terraform.io/docs/providers/aws/r/acm_certificate_validation.html
[2] https://www.terraform.io/docs/configuration/modules.html#passing-providers-explicitly

*/

resource "aws_acm_certificate" "https_certificate" {
  domain_name               = var.domains[0].domain
  subject_alternative_names = [for tuple in slice(var.domains, 1, length(var.domains)) : tuple.domain]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "https_certificate_validation_record" {
  count   = length(var.domains)
  name    = lookup(aws_acm_certificate.https_certificate.domain_validation_options[count.index], "resource_record_name")
  type    = lookup(aws_acm_certificate.https_certificate.domain_validation_options[count.index], "resource_record_type")
  records = ["${lookup(aws_acm_certificate.https_certificate.domain_validation_options[count.index], "resource_record_value")}"]
  zone_id = lookup(var.domains[count.index], "zone_id")
  ttl     = 60
}

# This version of the HTTPS certificate blocks until it is validated [1].
resource "aws_acm_certificate_validation" "https_certificate" {
  certificate_arn         = aws_acm_certificate.https_certificate.arn
  validation_record_fqdns = aws_route53_record.https_certificate_validation_record.*.fqdn
}
