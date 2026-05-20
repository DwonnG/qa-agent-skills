# Filtering Resources

How to translate user requests into AWS CLI queries.

## Lambda Functions

### List all functions

```bash
scripts/aws-cli --profile <PROFILE> lambda list-functions --region <region> \
  --query 'Functions[].FunctionName' --output json
```

### Filter by prefix

```bash
scripts/aws-cli --profile <PROFILE> lambda list-functions --region <region> \
  --query "Functions[?starts_with(FunctionName, 'app_')].FunctionName" --output json
```

### Filter by exact names

No special query needed. Just use each name directly in metric calls:
```bash
scripts/aws-cli --profile <PROFILE> cloudwatch get-metric-statistics ... --dimensions Name=FunctionName,Value=app_enricher_container ...
```

### Filter by tag

Two-step process:

1. List candidate functions (by prefix or all)
2. Check each function's tags:

```bash
scripts/aws-cli --profile <PROFILE> lambda get-function --function-name <name> \
  --query 'Tags.ResourceOwner' --output text --region <region>
```

To filter to a specific tag value (e.g., `ResourceOwner=TeamA`):
- Fetch the tag for each function
- Include only those matching the target value

To filter to multiple tag values (e.g., all teams in a capability group):
- User provides the list: "TeamA, TeamB"
- Check each function's tag against that list

### Get all tags at once

```bash
scripts/aws-cli --profile <PROFILE> lambda get-function --function-name <name> \
  --query 'Tags' --output json --region <region>
```

Useful tags: `ResourceOwner` (team), `subsystem`, `component`, `repository`

## API Gateways

### List all APIs

```bash
scripts/aws-cli --profile <PROFILE> apigateway get-rest-apis --region <region> \
  --query 'items[].[name,id]' --output json
```

### Filter by prefix

```bash
scripts/aws-cli --profile <PROFILE> apigateway get-rest-apis --region <region> \
  --query "items[?starts_with(name, 'app_')].[name,id]" --output json
```

### Get tags for an API Gateway

API Gateway tags require the ARN:

```bash
# Build ARN from region, account, and API ID
scripts/aws-cli --profile <PROFILE> apigateway get-tags \
  --resource-arn "arn:aws:apigateway:<region>::/restapis/<api-id>" \
  --region <region> --output json
```

## Common Filter Patterns

| User says | What to do |
|-----------|------------|
| "compare app_enricher" | Use exact name, no discovery needed |
| "compare all qa lambdas" | List with `starts_with(FunctionName, 'app_')` |
| "compare lambdas owned by TeamA" | List all, filter by `ResourceOwner=TeamA` tag |
| "compare Platform resources" | Ask user which teams are in Platform, then filter by those ResourceOwner values |
| "compare enricher and directory API" | Use two exact names; mix Lambda and API Gateway if needed |
| "compare everything in us-east-1" | List all functions and APIs, no filter |

## Performance Note

Fetching tags one function at a time is slow for large inventories. Strategies:
- Filter by prefix first to reduce the candidate set
- Ask the user to provide specific names if they know them
- Cache tag results within a session (don't re-fetch)
