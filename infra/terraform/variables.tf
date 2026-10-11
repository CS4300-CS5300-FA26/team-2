variable "location" {
  description = "Azure region for all resources. Must be on this subscription's region allow-list policy (check with: az policy assignment list)."
  type        = string
  default     = "westus"
}

variable "project_name" {
  description = "Short name used as a prefix for all resource names."
  type        = string
  default     = "pathfinder"
}

variable "environment" {
  description = "Environment tag/suffix (prod, staging, etc)."
  type        = string
  default     = "prod"
}
