variable "package_slug" {
  description = "The package name as a slug in snake_case."
  type        = string
}

variable "package-slug" {
  description = "The package name as a slug in kebab-case."
  type        = string
}

variable "package_version" {
  description = "The package version."
  type        = string
}

variable "git_branch" {
  description = "The branch this package version is based on."
  type        = string
}

variable "organisation_account" {
  description = "The organisation account id."
  type        = string
}

variable "workspace_accounts" {
  description = "The account ids of the workspace accounts."
  type        = map(string)
}

variable "region" {
  description = "The cloud region to deploy to."
  type        = string
}

variable "deploy" {
  description = "A JSON string with deployment information to be included in the runtime config."
  type        = string
}
