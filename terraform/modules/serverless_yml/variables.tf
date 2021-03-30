variable "region" {
  description = "The AWS region to deploy the Lambda function in."
  type        = string
}

variable "domain" {
  description = "The domain the API is hosted on."
  type        = string
}

variable "hosted_zone" {
  description = "The domain's hosted zone in which the DNS record to the Lambda function will be created."
  type        = string
}

variable "https_certificate" {
  description = "The HTTPS certificate ARN used with the domain."
  type        = string
}
