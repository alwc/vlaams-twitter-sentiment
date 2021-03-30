variable "bucket_name" {
  description = "The name of S3 bucket."
  type        = string
}

variable "versioning" {
  description = "Whether to enable versioning."
  type        = bool
  default     = true
}

variable "website" {
  description = "Whether to create the S3 bucket with Website Hosting."
  type        = bool
  default     = false
}
