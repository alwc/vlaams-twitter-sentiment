/*

# Purpose

Create a CDN that:

   1. Redirects http://{domain} to https://{domain}.
   2. Adds origins that you provide, such as an S3 website or API Gateway.
   3. Adds a default cached behavior and ordered cache behaviors for (2) that enables caching and
      compression.
   4. Attaches Lambda@Edge pre/post request processing helper functions.

Note: you may only supply one origin with a `path_pattern` of `null`, because this module associates
the `default_cache_behavior` with that origin and a CloudFront distribution can have only one
default cache behavior [1].

# Usage

module "s3_website_bucket" {
  source      = "./modules/s3_bucket"
  bucket_name = local.workspace_domain
  website     = true
}

module "cloudfront_cdn" {
  source            = "./modules/cloudfront_distribution"
  domain            = local.workspace_domain
  https_certificate = module.https_certificate.https_certificate
  hosted_zone       = aws_route53_zone.workspace_domain.zone_id

  origins = {
    "${module.s3_website_bucket.website_endpoint}" : {
      path_pattern : null,
      origin_type : "S3_WEBSITE",
      function_associations: []
    },
    "${local.workspace_api_domain}" : {
      path_pattern : "/api*",
      origin_type : "API_GATEWAY",
      function_associations: []
    }
  }
}

# References

[1] https://www.terraform.io/docs/providers/aws/r/cloudfront_distribution.html#default_cache_behavior
[2] https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DefaultRootObject.html
[3] https://stackoverflow.com/questions/55040555/terraform-cant-create-a-cloudfronts-origin-with-a-static-s3-website-endpoint

*/

locals {
  origin_settings = {
    # We must use a custom Origin pointing to the Website Hosting endpoint of the S3 bucket, because
    # we want to use S3's default root object handling and not CloudFront's default root object
    # handling [2].
    S3_WEBSITE : {
      # CloudFront must communicate over HTTP with the S3 website endpoint [3].
      protocol_policy : "http-only",
      allowed_methods : ["GET", "HEAD", "OPTIONS"],
      cached_methods : ["GET", "HEAD", "OPTIONS"],
      forwarded_values : {
        headers : null,
        cookies : "none",
        query_string : false
      }
    },
    API_GATEWAY : {
      protocol_policy : "https-only",
      allowed_methods : ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
      cached_methods : ["GET", "HEAD"],
      forwarded_values : {
        headers : ["Accept", "Accept-Charset", "Accept-Datetime", "Accept-Encoding", "Accept-Language", "Access-Control-Request-Headers", "Access-Control-Request-Method", "Authorization", "Origin", "Referer"],
        cookies : "all",
        query_string : true
      }
    }
  }
}

resource "aws_cloudfront_distribution" "cdn" {
  wait_for_deployment = false
  enabled             = true
  is_ipv6_enabled     = true
  price_class         = "PriceClass_100" # CDN in EU & US (cheapest)
  aliases             = ["${var.domain}"]

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html#secure-connections-supported-ciphers
  viewer_certificate {
    acm_certificate_arn      = var.https_certificate
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.1_2016"
  }

  # Origins

  dynamic "origin" {
    for_each = var.origins
    content {
      domain_name = origin.key
      origin_id   = origin.key
      custom_origin_config {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = local.origin_settings[origin.value.origin_type].protocol_policy
        origin_ssl_protocols   = ["TLSv1.1", "TLSv1.2"]
      }
    }
  }

  # Behaviors

  dynamic "default_cache_behavior" {
    for_each = {
      for domain, origin_properties in var.origins :
      domain => local.origin_settings[origin_properties.origin_type] if origin_properties.path_pattern == null
    }
    content {
      target_origin_id = default_cache_behavior.key
      allowed_methods  = default_cache_behavior.value.allowed_methods
      cached_methods   = default_cache_behavior.value.cached_methods
      forwarded_values {
        query_string = default_cache_behavior.value.forwarded_values.query_string
        cookies {
          forward = default_cache_behavior.value.forwarded_values.cookies
        }
        headers = default_cache_behavior.value.forwarded_values.headers
      }

      viewer_protocol_policy = "redirect-to-https"
      compress               = true
    }
  }

  dynamic "ordered_cache_behavior" {
    for_each = {
      for domain, origin_properties in var.origins :
      domain => merge(local.origin_settings[origin_properties.origin_type], origin_properties) if origin_properties.path_pattern != null
    }
    content {
      target_origin_id = ordered_cache_behavior.key
      path_pattern     = ordered_cache_behavior.value.path_pattern
      allowed_methods  = ordered_cache_behavior.value.allowed_methods
      cached_methods   = ordered_cache_behavior.value.cached_methods
      forwarded_values {
        query_string = ordered_cache_behavior.value.forwarded_values.query_string

        cookies {
          forward = ordered_cache_behavior.value.forwarded_values.cookies
        }
        headers = ordered_cache_behavior.value.forwarded_values.headers
      }

      viewer_protocol_policy = "redirect-to-https"
      compress               = true
      dynamic "lambda_function_association" {
        for_each = ordered_cache_behavior.value.function_associations
        content {
          event_type   = lambda_function_association.value.event_type
          lambda_arn   = lambda_function_association.value.lambda_arn
          include_body = lambda_function_association.value.include_body
        }
      }
    }
  }
}

# https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html
resource "aws_route53_record" "cdn_alias_record" {
  name    = var.domain
  zone_id = var.hosted_zone
  type    = "A"

  alias {
    evaluate_target_health = false
    name                   = aws_cloudfront_distribution.cdn.domain_name
    zone_id                = aws_cloudfront_distribution.cdn.hosted_zone_id
  }
}
