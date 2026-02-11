# Pipeline Debugging — Runs, Logs & Triggers

> Load this file when the user asks about pipeline status, failed builds, viewing logs, triggering pipelines, or retrying runs.

## List Recent Runs

```powershell
az pipelines runs list --top 10 --output table
az pipelines runs list --pipeline-ids PIPELINE_ID --result failed --top 5 --output table
```

## View Run Details and Logs

```powershell
# Show run summary
az pipelines runs show --id RUN_ID --output table

# Get logs via REST (no direct CLI command for logs)
az devops invoke `
  --area pipelines `
  --resource logs `
  --route-parameters project=$config.project pipelineId=PIPELINE_ID runId=RUN_ID `
  --api-version 7.0
```

## Trigger and Retry

```powershell
# Trigger a pipeline
az pipelines run --name "pipeline-name" --branch main

# Trigger with variables
az pipelines run --name "pipeline-name" --variables "env=staging" "deploy=true"
```

## Download Artifacts

```powershell
az pipelines runs artifact download `
  --run-id RUN_ID `
  --artifact-name "drop" `
  --path ./artifacts
```

## View Pipeline Definition

```powershell
az pipelines show --name "CI Build" --output yaml
```
