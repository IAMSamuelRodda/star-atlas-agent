# Core Infrastructure Outputs

output "environment" {
  description = "Current environment name"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region where resources are deployed"
  value       = var.aws_region
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

# Will be populated as we add modules:
# - S3 bucket names and ARNs
# - DynamoDB table names and ARNs
# - Lambda function ARNs
# - API Gateway URLs
# - CloudFront distribution domain
