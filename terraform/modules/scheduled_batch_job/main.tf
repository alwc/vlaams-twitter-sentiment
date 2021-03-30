/*
# Purpose
Create a scheduled batch job with:
  1. A compute environment that scales from zero to var.max_vcpus with spot
     instances and back depending on the job pressure [1].
  2. A job queue to place jobs on.
  3. A job definition for jobs [2].
  4. Schedules the job on a given cron schedule [3] based on [4].
# Usage
module "scheduled_batch_job" {
  source               = "github.com/radix-ai/terraform-modules//scheduled_batch_job"
  name                 = "my-application"
  max_vcpus            = 16
  schedule_expression  = "cron(15 10 * * ? *)"  # 10:15 AM (UTC) every day
  container_properties = <<CONTAINER_PROPERTIES
{
    "command": ["ls", "-la"],
    "image": "busybox",
    "memory": 1024,
    "vcpus": 1,
    "volumes": [
      {
        "host": {
          "sourcePath": "/tmp"
        },
        "name": "tmp"
      }
    ],
    "environment": [
        {"name": "VARNAME", "value": "VARVAL"}
    ],
    "mountPoints": [
        {
          "sourceVolume": "tmp",
          "containerPath": "/tmp",
          "readOnly": false
        }
    ],
    "ulimits": [
      {
        "hardLimit": 1024,
        "name": "nofile",
        "softLimit": 1024
      }
    ]
}
CONTAINER_PROPERTIES
}
# References
[1] https://github.com/QuiNovas/terraform-aws-batch-compute-environment/blob/master/main.tf
[2] https://docs.aws.amazon.com/batch/latest/APIReference/API_RegisterJobDefinition.html
[3] https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchevents-expressions.html
[4] https://github.com/turnerlabs/terraform-scheduled-batch-job
*/

data "aws_availability_zones" "available" {
  state = "available"
}

module "batch_compute_environment" {
  # TODO: Expose the options below as variables.
  # TODO: Expose outputs.
  # TODO: https://github.com/QuiNovas/terraform-aws-batch-compute-environment/issues/8
  source                 = "QuiNovas/batch-compute-environment/aws"
  name                   = "${var.name}-compute-environment"
  type                   = "MANAGED"
  compute_resources_type = "SPOT"
  instance_type          = var.instance_type
  # Default is ["optimal"].
  bid_percentage     = 100
  min_vcpus          = 0
  desired_vcpus      = 0
  max_vcpus          = var.max_vcpus
  availability_zones = data.aws_availability_zones.available.names
  cidr_block         = "10.0.0.0/16"
}

resource "aws_batch_job_queue" "job_queue" {
  name     = "${var.name}-job-queue"
  state    = "ENABLED"
  priority = 1
  # Job queues with a higher priority are evaluated first.
  compute_environments = [
    module.batch_compute_environment.arn
  ]
}

resource "aws_batch_job_definition" "job_definition" {
  name                 = "${var.name}-job-definition"
  type                 = "container"
  container_properties = var.container_properties
}

# Inlined [4] because it is outdated and made the following changes:
# - Upgraded deprecated Lambda runtime nodejs6.10 to nodejs12.x.
# - Removed tags.
# - Removed unnecessary string interpolation.
# - Replaced data.template_file with templatefile.
# - Changed var.is_enabled from string to boolean.
module "schedule_batch_job" {
  source               = "./schedule_batch_job"
  name                 = "${var.name}-job"
  batch_job_definition = aws_batch_job_definition.job_definition.arn
  batch_job_queue      = aws_batch_job_queue.job_queue.arn
  schedule_expression  = var.schedule_expression
}