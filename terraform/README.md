# Terraform Infrastructure

Infrastructure as Code for Star Atlas Agent AWS deployment.

## Structure

```
terraform/
├── versions.tf          # Terraform and provider versions, backend config
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── modules/             # Reusable Terraform modules
│   ├── lambda/          # Lambda function module (TBD)
│   ├── dynamodb/        # DynamoDB table module (TBD)
│   └── ecs/             # ECS Fargate service module (TBD)
└── environments/        # Environment-specific configurations
    ├── dev/
    │   ├── backend.tfvars      # S3 backend config for dev
    │   └── terraform.tfvars    # Variable values for dev
    ├── staging/
    └── prod/
```

## Prerequisites

1. **Terraform** >= 1.6.0
   ```bash
   brew install terraform  # macOS
   # or download from https://www.terraform.io/downloads
   ```

2. **AWS CLI** configured with credentials
   ```bash
   aws configure
   ```

3. **S3 Backend Bucket** (one-time manual setup)
   ```bash
   # Create S3 bucket for Terraform state
   aws s3api create-bucket \
     --bucket star-atlas-agent-terraform-state-dev \
     --region us-east-1

   # Enable versioning
   aws s3api put-bucket-versioning \
     --bucket star-atlas-agent-terraform-state-dev \
     --versioning-configuration Status=Enabled

   # Create DynamoDB table for state locking
   aws dynamodb create-table \
     --table-name star-atlas-agent-terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST \
     --region us-east-1
   ```

## Usage

### Initialize Terraform (First Time)

```bash
cd terraform/

# Initialize with dev backend configuration
terraform init -backend-config=environments/dev/backend.tfvars
```

### Plan Changes

```bash
# Review changes for dev environment
terraform plan -var-file=environments/dev/terraform.tfvars
```

### Apply Changes

```bash
# Apply changes to dev environment
terraform apply -var-file=environments/dev/terraform.tfvars
```

### Destroy Infrastructure

```bash
# Destroy dev environment (use with caution!)
terraform destroy -var-file=environments/dev/terraform.tfvars
```

## Environment Configuration

### Development (dev)
- Cost-optimized: Voice service and memory system disabled by default
- Purpose: Local development and testing
- Target cost: <$5/month

### Staging (staging)
- Full feature set enabled
- Purpose: Pre-production testing
- Target cost: ~$30/month

### Production (prod)
- Full feature set with optimizations
- Purpose: Live user traffic
- Target cost: ~$20-25/month (optimized)

## Cost Controls

The infrastructure uses feature flags to control costs:

- `enable_voice_service`: ECS Fargate for WebRTC (~$3-5/month)
- `enable_memory_system`: DynamoDB vector store + Bedrock (~$20-25/month)

**Development tip**: Keep these disabled until you're ready to test those features.

## State Management

- **Backend**: S3 with DynamoDB locking
- **Encryption**: Enabled for state files
- **Versioning**: Enabled on S3 bucket for state history
- **Locking**: DynamoDB prevents concurrent modifications

## Next Steps

1. Complete Lambda Functions Infrastructure (Issue #4)
2. Complete DynamoDB Tables Schema (Issue #5)
3. Complete S3 + CloudFront for Frontend (Issue #6)

## Troubleshooting

### Error: "Backend initialization required"
```bash
terraform init -backend-config=environments/dev/backend.tfvars -reconfigure
```

### Error: "S3 bucket does not exist"
Run the S3 backend bucket setup commands in the Prerequisites section.

### Error: "Access Denied"
Ensure your AWS credentials are configured:
```bash
aws sts get-caller-identity  # Verify your AWS identity
```

## Security Notes

- Never commit `.tfstate` files to git (already in `.gitignore`)
- Never commit AWS credentials
- Use IAM roles with least privilege
- Enable MFA for AWS account
