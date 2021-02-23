provider "aws" {
  profile = "default"
  region  = "eu-west-1"
}

# cloudwatch log group met terraform pipeline
resource "aws_cloudwatch_log_group" "tome-vo-vsa-twitter-tst-loggroup" {
  name = "tome-vo-vsa-twitter-tst-loggroup"

  tags = {
    Environment = "tst"
    Application = "terraform-codepipeline-test"
  }
}
