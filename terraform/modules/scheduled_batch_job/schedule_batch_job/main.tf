/**
 * A Terraform module representing a scheduled Batch job. Uses a Cloud Watch Event Rule and a Lambda function to submit the Batch job on a cron schedule
*/

# the name of the scheduled job
variable "name" {}

# the batch job definition to run
variable "batch_job_definition" {}

# the batch job queue to submit to
variable "batch_job_queue" {}

# the schedule to execute the job on
variable "schedule_expression" {}

# whether or not the job will be run
variable "is_enabled" {
  default = true
}

data "archive_file" "lambda_zip" {
  type = "zip"
  source_content = templatefile("${path.module}/index.js", {
    name                 = var.name
    batch_job_definition = var.batch_job_definition
    batch_job_queue      = var.batch_job_queue
  })
  source_content_filename = "index.js"
  output_path             = "lambda-${var.name}.zip"
}

resource "aws_lambda_function" "func" {
  function_name    = var.name
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = aws_iam_role.role.arn
  handler          = "index.handler"
  runtime          = "nodejs12.x"
}

resource "aws_lambda_permission" "permission" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.func.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rule.arn
}

resource "aws_lambda_alias" "alias" {
  name             = var.name
  description      = ""
  function_name    = aws_lambda_function.func.function_name
  function_version = "$LATEST"
}

# cloud watch scheduled event
resource "aws_cloudwatch_event_rule" "rule" {
  name                = var.name
  description         = "fires the ${var.name} function on schedule: ${var.schedule_expression}"
  schedule_expression = var.schedule_expression
  is_enabled          = var.is_enabled
}

resource "aws_cloudwatch_event_target" "target" {
  rule = aws_cloudwatch_event_rule.rule.name
  arn  = aws_lambda_function.func.arn
}

resource "aws_iam_role" "role" {
  name = var.name

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_policy" "batch" {
  name        = "${var.name}-batch"
  description = ""

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Action": [
        "batch:DescribeJobs",
        "batch:ListJobs",
        "batch:SubmitJob"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda-batch" {
  role       = aws_iam_role.role.name
  policy_arn = aws_iam_policy.batch.arn
}

resource "aws_iam_role_policy_attachment" "lambda-cw" {
  role       = aws_iam_role.role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# the created cloudwatch event rule
output "cloudwatch_event_rule_arn" {
  value = aws_cloudwatch_event_rule.rule.arn
}

# the created lambda function
output "aws_lambda_function_arn" {
  value = aws_lambda_function.func.arn
}