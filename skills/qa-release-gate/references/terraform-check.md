# Terraform Deployment Check

How to verify whether a TeamA feature has been deployed to the integration environment.

## Per-Repo Check Logic

### policy-service — Pinned (manual bump required)

`service_version` is NOT set to `latest` in `integration.tfvars`. It uses the **default** from `non_production/variables.tf`, which must be explicitly bumped.

The policy-service release Jenkinsfile opens a terraform PR that bumps the version in both `non_production/variables.tf` and `production/variables.tf`.

**Check**:
```bash
gh pr list --repo github.com/your-org/terraform --state merged --search "service_version" --limit 5 --json number,title,mergedAt
```

If no recent merged PR bumps the version, the feature is likely NOT deployed to integration yet.

### api-service — Auto-deploys (latest)

`non_production/integration.tfvars` sets:
```
service_version = "latest"
```

This means integration picks up the latest image tag automatically on the next terraform apply. No manual version bump needed.

**Check**: Confirm the terraform pipeline has run recently after the api-service PR merged. Look for recent Jenkins runs of the integration deployment job.

### frontend-app — No terraform dependency

Frontend repo deployed independently. Skip this check.

### directory-data — No terraform dependency

No terraform version variable exists for directory-data. Skip this check.

### docs-repo — No terraform dependency

Documentation repo with no deployment. Skip this check.

## Version Format

All version strings follow the pattern: `YYYYMMDD.HHMM-<12-char-hex>` (e.g., `20260331.1731-5465490b3e45`). The special value `latest` pulls the most recent image.

## Deployment Pipeline

After a terraform PR merges to main:
1. `terraform_pr_gate.jenkinsfile` packages the terraform module
2. `release-platform-environment` creates a release
3. `deploy_platform_environment` deploys to integration (and fedinteg)

The full chain: **app release** (image in Artifactory) → **terraform version bump** (PR) → **terraform merge** → **deploy pipeline** → **integration live**.

For api-service with `latest`, the chain is simpler: **app release** (image with `latest` tag) → **next terraform apply** → **integration live**.
