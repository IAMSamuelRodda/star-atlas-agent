# Core Configuration Variables

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "star-atlas-agent"
}

# Application Configuration

variable "enable_voice_service" {
  description = "Enable ECS Fargate voice service (cost: ~$3-5/month)"
  type        = bool
  default     = false # Disabled for cost-conscious dev environment
}

variable "enable_memory_system" {
  description = "Enable DynamoDB vector store and memory system (cost: ~$20-25/month)"
  type        = bool
  default     = false # Disabled for initial setup
}

# Deployment Configuration

variable "deployment_id" {
  description = "Deployment identifier (commit SHA for version tracking)"
  type        = string
  default     = "initial"
}

# Tags

variable "tags" {
  description = "Default tags to apply to all resources"
  type        = map(string)
  default     = {
    Project   = "star-atlas-agent"
    ManagedBy = "terraform"
  }
}

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Authentication Configuration

variable "jwt_secret" {
  description = "Secret key for JWT token signing (store in AWS Secrets Manager for production)"
  type        = string
  sensitive   = true
}
