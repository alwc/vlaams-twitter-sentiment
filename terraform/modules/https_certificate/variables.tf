variable "domains" {
  description = "The list of domains on which you want to certify and their corresponding Route 53 Hosted Zone ID."
  type        = list(object({ domain = string, zone_id = string }))
}
