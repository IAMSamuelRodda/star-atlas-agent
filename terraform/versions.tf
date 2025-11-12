terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration for state management
  # Run `terraform init` with backend config for each environment:
  # terraform init -backend-config=environments/dev/backend.tfvars
  backend "s3" {
    # Configured per environment via backend.tfvars
    # bucket         = "star-atlas-agent-terraform-state-<env>"
    # key            = "terraform.tfstate"
    # region         = "us-east-1"
    # dynamodb_table = "star-atlas-agent-terraform-locks"
    # encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "star-atlas-agent"
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "https://github.com/IAMSamuelRodda/star-atlas-agent"
    }
  }
}
