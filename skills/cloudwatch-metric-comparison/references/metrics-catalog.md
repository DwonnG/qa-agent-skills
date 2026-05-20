# Metrics Catalog

Exact `aws cloudwatch get-metric-statistics` commands for each supported metric.

All commands use `--output json` for agent parsing. Replace placeholders:
- `<PROFILE>`: AWS profile selected in step 1 of the workflow
- `<fn>`: Lambda function name (e.g., `app_enricher_container`)
- `<api>`: API Gateway name (e.g., `app_internal_directory`)
- `<start>`: ISO 8601 start time
- `<end>`: ISO 8601 end time
- `<region>`: AWS region
- `<period>`: Aggregation period in seconds (86400 = 1 day)

**Always include `--profile <PROFILE>`** on every command to avoid using Bedrock credentials.

## Lambda Metrics

Namespace: `AWS/Lambda` | Dimension: `FunctionName`

### Invocations (Sum)

Total number of function invocations. Changes indicate volume shifts.

```bash
scripts/aws-cli --profile <PROFILE> cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=<fn> \
  --start-time <start> --end-time <end> \
  --period <period> --statistics Sum \
  --region <region> --output json
```

### Duration p99

99th percentile execution time in milliseconds. Increases may indicate new downstream calls or heavier processing.

```bash
scripts/aws-cli --profile <PROFILE> cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=<fn> \
  --start-time <start> --end-time <end> \
  --period <period> --extended-statistics p99 \
  --region <region> --output json
```

Response path: `.Datapoints[].ExtendedStatistics.p99`

### Errors (Sum)

Number of invocations that resulted in a function error.

```bash
scripts/aws-cli --profile <PROFILE> cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=<fn> \
  --start-time <start> --end-time <end> \
  --period <period> --statistics Sum \
  --region <region> --output json
```

### Throttles (Sum)

Number of invocations throttled due to concurrency limits.

```bash
scripts/aws-cli --profile <PROFILE> cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Throttles \
  --dimensions Name=FunctionName,Value=<fn> \
  --start-time <start> --end-time <end> \
  --period <period> --statistics Sum \
  --region <region> --output json
```

### ConcurrentExecutions (Maximum)

Peak concurrent invocations during the period.

```bash
scripts/aws-cli --profile <PROFILE> cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value=<fn> \
  --start-time <start> --end-time <end> \
  --period <period> --statistics Maximum \
  --region <region> --output json
```

## API Gateway Metrics

Namespace: `AWS/ApiGateway` | Dimension: `ApiName`

### Count (Sum)

Total API requests received.

```bash
scripts/aws-cli --profile <PROFILE> cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=<api> \
  --start-time <start> --end-time <end> \
  --period <period> --statistics Sum \
  --region <region> --output json
```

### 5XXError (Sum)

Server-side errors.

```bash
scripts/aws-cli --profile <PROFILE> cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 5XXError \
  --dimensions Name=ApiName,Value=<api> \
  --start-time <start> --end-time <end> \
  --period <period> --statistics Sum \
  --region <region> --output json
```

### 4XXError (Sum)

Client-side errors.

```bash
scripts/aws-cli --profile <PROFILE> cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 4XXError \
  --dimensions Name=ApiName,Value=<api> \
  --start-time <start> --end-time <end> \
  --period <period> --statistics Sum \
  --region <region> --output json
```

### Latency p99

99th percentile response time in milliseconds.

```bash
scripts/aws-cli --profile <PROFILE> cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Latency \
  --dimensions Name=ApiName,Value=<api> \
  --start-time <start> --end-time <end> \
  --period <period> --extended-statistics p99 \
  --region <region> --output json
```

Response path: `.Datapoints[].ExtendedStatistics.p99`

## Period Selection

- For windows spanning days: use `--period 86400` (1 day) to get daily aggregates
- For windows spanning hours: use `--period 3600` (1 hour)
- Compute the average of all datapoints in a window for comparison

## Parsing Datapoints

CloudWatch returns datapoints as an unordered array. To compute a window average:

1. Filter datapoints where `Timestamp` falls within the window
2. For Sum metrics: average the daily Sum values
3. For Maximum metrics: take the max across all datapoints
4. For p99: average the daily p99 values
