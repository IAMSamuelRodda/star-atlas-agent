# GitHub Secrets Migration Guide

This document outlines the required GitHub environment setup and secrets migration for proper separation between staging and production deployments.

## Environment Setup

Create two GitHub environments in your repository settings:

1. **staging** - For staging deployments
2. **production** - For production deployments

### Creating Environments

1. Go to repository **Settings** → **Environments**
2. Click **New environment**
3. Create `staging` environment
4. Create `production` environment

### Environment Protection Rules (Recommended)

**Staging Environment:**
- Deployment branch rule: `main` branch only (enforced in workflow)
- Optional: Add required reviewers for staging deployments
- Optional: Add wait timer for staging deployments

**Production Environment:**
- Deployment branch rule: `main` branch only (enforced in workflow)
- Recommended: Add required reviewers for production deployments
- Recommended: Add wait timer (e.g., 5 minutes) for production deployments

## Secrets Migration

### Repository-Level Secrets (Shared)

Keep these at the repository level (not environment-specific):

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AWS_REGION` | AWS region for all deployments | `us-west-2` |

### Staging Environment Secrets

Move these secrets to the **staging** environment:

| Secret Name | Current Location | New Location | Description |
|-------------|------------------|--------------|-------------|
| `AWS_ROLE_ARN_STAGING` | Repository | Staging Env | AWS IAM role for staging deployments |
| `STAGING_API_URL` | Repository | Staging Env | Staging API URL for health checks |
| `TEST_WALLET_STAGING` | Repository | Staging Env | Test wallet for staging E2E tests |

### Production Environment Secrets

Move these secrets to the **production** environment:

| Secret Name | Current Location | New Location | Description |
|-------------|------------------|--------------|-------------|
| `AWS_ROLE_ARN_PRODUCTION` | Repository | Production Env | AWS IAM role for production deployments |
| `PRODUCTION_API_URL` | Repository | Production Env | Production API URL for health checks |

## Migration Steps

### 1. Create Environments

```bash
# Using GitHub CLI
gh api repos/{owner}/{repo}/environments/staging -X PUT
gh api repos/{owner}/{repo}/environments/production -X PUT
```

Or manually via GitHub UI (Settings → Environments → New environment).

### 2. Add Secrets to Staging Environment

```bash
# Using GitHub CLI
gh secret set AWS_ROLE_ARN_STAGING --env staging
gh secret set STAGING_API_URL --env staging
gh secret set TEST_WALLET_STAGING --env staging
```

Or manually:
1. Go to **Settings** → **Environments** → **staging**
2. Click **Add secret**
3. Add each secret from the table above

### 3. Add Secrets to Production Environment

```bash
# Using GitHub CLI
gh secret set AWS_ROLE_ARN_PRODUCTION --env production
gh secret set PRODUCTION_API_URL --env production
```

Or manually:
1. Go to **Settings** → **Environments** → **production**
2. Click **Add secret**
3. Add each secret from the table above

### 4. Clean Up Old Repository Secrets

After migrating, delete the old repository-level secrets that are now environment-specific:

```bash
# Using GitHub CLI
gh secret delete AWS_ROLE_ARN_STAGING
gh secret delete STAGING_API_URL
gh secret delete TEST_WALLET_STAGING
gh secret delete AWS_ROLE_ARN_PRODUCTION
gh secret delete PRODUCTION_API_URL
```

**Keep** `AWS_REGION` at the repository level (shared across environments).

## Verification

After migration, verify secrets are correctly set:

```bash
# List repository secrets
gh secret list

# List staging environment secrets
gh secret list --env staging

# List production environment secrets
gh secret list --env production
```

Expected output:

**Repository secrets:**
- `AWS_REGION`

**Staging environment secrets:**
- `AWS_ROLE_ARN_STAGING`
- `STAGING_API_URL`
- `TEST_WALLET_STAGING`

**Production environment secrets:**
- `AWS_ROLE_ARN_PRODUCTION`
- `PRODUCTION_API_URL`

## Workflow Updates

The deployment workflows have been updated to use environment-specific secrets:

- `deploy-staging.yml` now uses `environment: staging`
- `deploy-production.yml` now uses `environment: production`
- Secrets are automatically scoped to the correct environment

## Security Benefits

1. **Least Privilege**: Production secrets are isolated from staging
2. **Audit Trail**: Environment-level deployments provide better audit logs
3. **Protection Rules**: Can add reviewers/wait times for production only
4. **Branch Controls**: Can restrict which branches can deploy to production

## Troubleshooting

**Error: "Secret not found"**
- Verify secret is set in the correct environment (not repository level)
- Check secret name matches exactly (case-sensitive)

**Error: "Environment not found"**
- Create the environment first via Settings → Environments
- Or use `gh api` command above to create programmatically

**Deployment fails with authentication error**
- Verify AWS role ARN is correct for the environment
- Check IAM role trust policy allows GitHub OIDC authentication
