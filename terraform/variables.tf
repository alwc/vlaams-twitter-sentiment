variable "package_slug" {
  description = "The package name as a slug in snake_case."
  type        = string
  default     = "sentiment_flanders"
}

variable "package-slug" {
  description = "The package name as a slug in kebab-case."
  type        = string
  default     = "sentiment_flanders"
}

variable "package_version" {
  description = "The package version."
  type        = string
  default     = "0.0.0"
}

variable "git_branch" {
  description = "The branch this package version is based on."
  type        = string
  default     = "master"
}

variable "organisation_account" {
  description = "The organisation account id."
  type        = string
  default     = "840374773521"
}

variable "workspace_accounts" {
  description = "The account ids of the workspace accounts."
  type        = map(string)
  default = {
    "infrastructure" : "840374773521",
    "feature" : "840374773521",
    "development" : "840374773521",
    "acceptance" : "840374773521",
    "production" : "840374773521",
    "default" : "840374773521"
  }
}

variable "region" {
  description = "The cloud region to deploy to."
  type        = string
  default     = "eu-west-1"
}
