# Deployment Configuration

Maps repositories to their deployed AWS Lambda functions per environment.

## Lambda Mapping

### api-service

| Environment | Lambda Functions |
|-------------|-----------------|
| integration | app_bulk_reclassification_container, app_bulk_remediation_container, app_webhook_action_container, app_enricher_container |
| qa | app_bulk_reclassification_container, app_bulk_remediation_container, app_webhook_action_container, app_enricher_container |

### policy-service

| Environment | Lambda Functions |
|-------------|-----------------|
| integration | integration_app_engine_api_container, integration_app_engine_validator_container |
| qa | app_app_engine_api_container, app_app_engine_validator_container |

### directory-data

| Environment | Lambda Functions |
|-------------|-----------------|
| integration | integration_internal_directory_api_container, integration_directory_data_sync_tasks_container, integration_directory_data_terminator_container, integration_directory_data_sync_scheduler_container |
| qa | app_internal_directory_api_container, app_directory_data_sync_tasks_container, app_directory_data_terminator_container, app_directory_data_sync_scheduler_container |

### frontend-app

| Environment | Lambda Functions |
|-------------|-----------------|
| integration | staging_frontend_ui_container |
| qa | app_frontend_ui_container |

## Usage

Use this mapping with AWS CLI to verify deployment timestamps:
```bash
AWS_PROFILE=app_engineer aws lambda get-function-configuration --function-name <FUNCTION_NAME> --query 'LastModified' --output text
```
