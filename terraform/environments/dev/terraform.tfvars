# Terraform Variables - Development Environment

environment = "dev"
aws_region  = "us-east-1"

# Cost-conscious dev environment - disable expensive features
enable_voice_service  = false
enable_memory_system  = false

additional_tags = {
  CostCenter = "development"
  Owner      = "samuel"
}
