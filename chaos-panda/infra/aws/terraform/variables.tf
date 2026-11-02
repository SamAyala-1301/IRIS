variable "project_name" {
  description = "Project name"
  type        = string
  default     = "chaospanda"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "owner" {
  description = "Owner tag"
  type        = string
  default     = "chaospanda-learning"
}
