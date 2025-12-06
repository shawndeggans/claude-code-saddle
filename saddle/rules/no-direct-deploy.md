# No Direct Deploy Policy

All infrastructure and deployment changes MUST go through Infrastructure as Code (IaC). Direct manual changes to production or staging environments are prohibited.

## Prohibited Actions

### Direct Cloud CLI Commands
- `aws` CLI commands that modify resources (create, update, delete)
- `gcloud` commands that modify resources
- `az` commands that modify resources
- `kubectl apply`, `kubectl delete`, `kubectl edit` against production

### Direct Console Changes
- Creating resources through cloud provider web consoles
- Modifying security groups, IAM policies, or network settings manually
- Scaling services without IaC updates

### Deployment Bypasses
- SSH into servers to deploy code
- Manual file uploads to S3/GCS/Azure Blob
- Direct database schema changes

## Approved Methods

### Infrastructure as Code Tools
- **Terraform**: Preferred for cloud infrastructure
- **Pulumi**: Acceptable alternative
- **CloudFormation**: For AWS-only projects
- **CDK**: If project already uses it

### Deployment Pipelines
- CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)
- ArgoCD for Kubernetes deployments
- Terraform Cloud/Enterprise for infrastructure

### Database Migrations
- Alembic for Python/SQLAlchemy
- Django migrations
- Flyway or Liquibase for JVM projects
- All migrations must be version-controlled

## Exception Process

If a direct change is absolutely necessary (emergency hotfix):

1. Document the change in an incident report
2. Create a follow-up ticket to codify the change in IaC
3. Apply the IaC change within 24 hours
4. Verify IaC matches the manual change

## Rationale

### Why This Matters
- Manual changes create configuration drift
- Undocumented changes are impossible to reproduce
- IaC enables disaster recovery and environment replication
- Code review for infrastructure changes catches errors

### Cost of Non-Compliance
- Environment inconsistencies
- Failed deployments when IaC doesn't match reality
- Security vulnerabilities from undocumented access
- Audit failures in regulated industries
