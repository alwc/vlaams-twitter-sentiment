variable "package_name" {
  description = "The package name under which the config is stored."
  type        = string
}

variable "package_version" {
  description = "The optional version specifier under which the config is stored."
  type        = string
  default     = "latest"
}

variable "deploy" {
  description = "A JSON object that contains the deployment information for this package."
}

variable "config" {
  description = "A JSON object that contains the runtime config for this package."
}

variable "tier" {
  description = "The tier of the parameter in the Parameter Store. Valid tiers are Standard and Advanced."
  type        = string
  default     = "Standard"
}

variable "type" {
  description = "The type of config string to be stored in the Parameter Store. Valid choices are String and SecureString."
  type        = string
  default     = "SecureString"
}
