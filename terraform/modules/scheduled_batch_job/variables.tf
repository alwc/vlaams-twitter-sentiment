variable "name" {
  description = "The name prefix to use for the compute environment, job queue, and job definition."
  type        = string
}

variable "max_vcpus" {
  description = "The maximum number of vCPUs in the compute environment (min. 0)."
  type        = number
  default     = 16
}

variable "instance_type" {
  description = "The instance types to use in the compute environment."
  type        = list(string)
  default     = ["optimal"]
}

variable "schedule_expression" {
  description = "The CloudWatch schedule expression to schedule the jobs with."
  type        = string
}

variable "container_properties" {
  description = "The JSON specification of the job definition."
  type        = string
}