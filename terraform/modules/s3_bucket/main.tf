/*

# Purpose

Create an S3 bucket [1] with:

  1. Encryption
  2. Versioning
  3. Acceleration [2]
  4. No public access (ACLs [3] and policies are blocked)
  5. Optional: Website Hosting [4] [5]

With Website Hosting enabled:

  1. Encryption is disabled
  2. Public read access is granted
  3. Static content must be hosted at the root of the bucket for compatibility
     with CloudFront distributions [6]
  4. CORS is enabled [7]

Note: if you enable Website Hosting, you cannot use periods in the bucket name because that is
incompatible with S3's transfer acceleration.

# Usage

module "s3_bucket" {
  source       = "./modules/s3_bucket"
  bucket_name  = "my_bucket"
}

module "s3_website_bucket" {
  source      = "./modules/s3_bucket"
  bucket_name = "my_bucket"
  versioning  = false
  website     = true
}

# References

[1] https://www.terraform.io/docs/providers/aws/r/s3_bucket.html
[2] https://docs.aws.amazon.com/AmazonS3/latest/dev/transfer-acceleration.html
[3] https://aws.amazon.com/blogs/security/iam-policies-and-bucket-policies-and-acls-oh-my-controlling-access-to-s3-resources/
[4] https://docs.aws.amazon.com/AmazonS3/latest/dev/EnableWebsiteHosting.html
[5] https://www.terraform.io/docs/providers/aws/r/s3_bucket.html#static-website-hosting
[6] https://forums.aws.amazon.com/thread.jspa?threadID=265796
[7] https://docs.aws.amazon.com/AmazonS3/latest/API/API_CORSRule.html

*/

resource "aws_s3_bucket_public_access_block" "s3_no_public_access" {
  bucket                  = local.bucket_name
  block_public_acls       = true
  block_public_policy     = !var.website
  ignore_public_acls      = true
  restrict_public_buckets = !var.website
}

locals {
  encryption_algorithm = var.website ? [] : ["AES256"]
  website_page = var.website ? [{
    index_document = "index.html"
    error_document = "error.html"
  }] : []
}

resource "aws_s3_bucket" "instance" {
  bucket = var.bucket_name

  tags = {
    environment = "prd"
    support = "standard"
  }


  dynamic "server_side_encryption_configuration" {
    for_each = local.encryption_algorithm
    content {
      rule {
        apply_server_side_encryption_by_default {
          sse_algorithm = server_side_encryption_configuration.value
        }
      }
    }
  }

  dynamic "website" {
    for_each = local.website_page
    content {
      index_document = website.value.index_document
      error_document = website.value.error_document
    }
  }

  dynamic "cors_rule" {
    for_each = local.website_page
    content {
      allowed_headers = ["*"]
      allowed_methods = ["GET"]
      allowed_origins = ["*"]
      expose_headers  = ["ETag"]
      max_age_seconds = 3600
    }
  }

  policy = !var.website ? null : <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPublicRead",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${var.bucket_name}/*"
    }
  ]
}
EOF

  versioning {
    enabled = var.versioning
  }

  acceleration_status = "Enabled"
}

locals {
  bucket_name      = aws_s3_bucket.instance.id
  website_endpoint = var.website ? aws_s3_bucket.instance.website_endpoint : null
}
