terraform {
  backend "s3" {
    bucket = "vo-vsa-twitter-state-bucket"
    key = "terraform.tfstate"
    encrypt = true
    region = "eu-west-1"
  }
}