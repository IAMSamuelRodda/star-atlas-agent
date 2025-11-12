# Terraform Backend Configuration - Development Environment
# Usage: terraform init -backend-config=environments/dev/backend.tfvars

bucket         = "star-atlas-agent-terraform-state-dev"
key            = "dev/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "star-atlas-agent-terraform-locks"
encrypt        = true
