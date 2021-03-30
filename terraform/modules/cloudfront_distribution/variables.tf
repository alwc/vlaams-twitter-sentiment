variable "domain" {
  description = "The domain on which you want to host the static content and API."
  type        = string
}

variable "https_certificate" {
  description = "The HTTPS certificate ARN that applies to the domain."
  type        = string
}

variable "hosted_zone" {
  description = "The Route 53 Hosted Zone ID where to create a record that points to this CDN."
  type        = string
}

variable "origins" {
  description = "Dynamic origin properties"
  type = map(object({
    path_pattern = string
    origin_type  = string # One of S3_WEBSITE, API_GATEWAY
    function_associations = list(object({
      event_type   = string # One of viewer-request, origin-request, viewer-response, origin-response
      lambda_arn   = string
      include_body = bool
    }))
  }))
}
