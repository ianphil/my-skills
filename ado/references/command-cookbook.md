# az devops Command Cookbook

Verified command patterns for common ADO operations. Copy-paste ready.

## Work Items

### Create

```powershell
# User Story
az boards work-item create \
  --type "User Story" \
  --title "Implement login page" \
  --description "As a user, I want to log in so I can access my account." \
  --assigned-to "user@example.com" \
  --area "Secure Cloud Access\Azure Encrypted Transport\SWE" \
  --iteration "Secure Cloud Access\Krypton"

# Bug
az boards work-item create \
  --type Bug \
  --title "Login button unresponsive on mobile" \
  --description "<p>Steps to reproduce:</p><ol><li>Open mobile browser</li><li>Tap login</li></ol>" \
  --assigned-to "user@example.com"

# Feature (create then link to parent epic)
$featureId = az boards work-item create \
  --type Feature \
  --title "User Authentication" \
  --area "Secure Cloud Access\Azure Encrypted Transport\SWE" \
  --iteration "Secure Cloud Access\Krypton" \
  --query "id" -o tsv
az boards work-item relation add --id $featureId --relation-type parent --target-id EPIC_ID

# Task under a Story (create then link)
$taskId = az boards work-item create \
  --type Task \
  --title "Write unit tests for auth module" \
  --query "id" -o tsv
az boards work-item relation add --id $taskId --relation-type parent --target-id STORY_ID
```

### Parent-Child Linking

There is no `--parent` flag on `az boards work-item create`. Use `relation add` after creation:

```powershell
# Link child to parent
az boards work-item relation add --id CHILD_ID --relation-type parent --target-id PARENT_ID

# Link multiple children to same parent
az boards work-item relation add --id PARENT_ID --relation-type child --target-id CHILD1,CHILD2,CHILD3

# View relations on a work item
az boards work-item relation show --id 12345 --output table
```

### Read

```powershell
# Show single item
az boards work-item show --id 12345 --output table

# Show with all relations/links
az boards work-item show --id 12345 --expand relations

# Note: --fields and --expand cannot be used together
```

### Update

```powershell
# Change state
az boards work-item update --id 12345 --state Active
az boards work-item update --id 12345 --state Closed

# Reassign
az boards work-item update --id 12345 --assigned-to "other@example.com"

# Update title and description
az boards work-item update --id 12345 \
  --title "Updated title" \
  --description "Updated description"

# Add tags
az boards work-item update --id 12345 --fields "System.Tags=api,backend,priority"

# Move to different area/iteration
az boards work-item update --id 12345 \
  --area "Project\NewTeam" \
  --iteration "Project\Sprint 2"

# Update custom fields using --fields
az boards work-item update --id 12345 \
  --fields "Microsoft.VSTS.Scheduling.StoryPoints=5"
```

### Delete

```powershell
# Delete (moves to recycle bin)
az boards work-item delete --id 12345 --yes

# Permanently destroy (cannot undo)
az boards work-item delete --id 12345 --destroy --yes
```

### Bulk Operations (PowerShell)

```powershell
# Bulk create stories under a feature
$featureId = 12345
$stories = @(
  "Setup authentication middleware",
  "Create login endpoint",
  "Create logout endpoint",
  "Add token refresh logic"
)
$stories | ForEach-Object {
  $storyId = az boards work-item create --type "User Story" --title $_ `
    --area "Secure Cloud Access\Azure Encrypted Transport\SWE" `
    --iteration "Secure Cloud Access\Krypton" `
    --query "id" -o tsv
  az boards work-item relation add --id $storyId --relation-type parent --target-id $featureId
}

# Bulk close items by query
$ids = az boards query --wiql "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Resolved'" --output json | ConvertFrom-Json
$ids | ForEach-Object { az boards work-item update --id $_.id --state Closed }

# Bulk assign
@(100, 101, 102) | ForEach-Object {
  az boards work-item update --id $_ --assigned-to "dev@example.com"
}
```

## Pull Requests

### Create

```powershell
# Basic PR
az repos pr create \
  --title "feat: add user authentication" \
  --description "Implements OAuth2 login flow. Resolves AB#12345"

# PR with full options
az repos pr create \
  --title "feat: add user authentication" \
  --description "Implements OAuth2 login flow" \
  --source-branch feature/12345-auth \
  --target-branch main \
  --work-items 12345 12346 \
  --reviewers "reviewer@example.com" \
  --auto-complete true \
  --delete-source-branch true \
  --squash true

# Draft PR
az repos pr create \
  --title "WIP: refactoring auth module" \
  --draft
```

### Review and Manage

```powershell
# List active PRs
az repos pr list --status active --output table

# List my PRs
az repos pr list --creator "user@example.com" --output table

# List PRs assigned to me for review
az repos pr list --reviewer "user@example.com" --output table

# Show PR details
az repos pr show --id 42 --output table

# View PR policies/checks status
az repos pr policy list --id 42 --output table

# Approve (vote=10)
az repos pr set-vote --id 42 --vote 10

# Approve with suggestions (vote=5)
az repos pr set-vote --id 42 --vote 5

# Waiting for author (vote=-5)
az repos pr set-vote --id 42 --vote -5

# Reject (vote=-10)
az repos pr set-vote --id 42 --vote -10

# Reset vote (vote=0)
az repos pr set-vote --id 42 --vote 0

# Complete/merge PR
az repos pr update --id 42 --status completed

# Abandon PR
az repos pr update --id 42 --status abandoned

# Add reviewer
az repos pr reviewer add --id 42 --reviewers "reviewer@example.com"

# Add comment (use REST via az devops invoke)
az devops invoke \
  --area git \
  --resource pullRequestThreads \
  --route-parameters project=PROJECT repositoryId=REPO pullRequestId=42 \
  --api-version 7.0 \
  --http-method POST \
  --in-file comment.json
```

### PR Work Item Linking

```powershell
# Link work items when creating PR
az repos pr create --title "fix: resolve bug" --work-items 12345 12346

# Add work item link to existing PR
az repos pr work-item add --id 42 --work-items 12345

# List linked work items
az repos pr work-item list --id 42 --output table
```

## Pipelines

### List and View

```powershell
# List all pipelines (get pipeline IDs from here)
az pipelines list --output table

# List runs for a specific pipeline (use --pipeline-ids, not --pipeline-name)
az pipelines runs list --pipeline-ids PIPELINE_ID --top 10 --output table

# List only failed runs (use --result, not --status for outcomes)
az pipelines runs list --pipeline-ids PIPELINE_ID --result failed --top 5 --output table

# List runs for a branch
az pipelines runs list --branch refs/heads/main --top 5 --output table

# Show run details
az pipelines runs show --id RUN_ID --output table
```

### Trigger

```powershell
# Run default branch
az pipelines run --name "CI Build"

# Run specific branch
az pipelines run --name "CI Build" --branch feature/auth

# Run with variables
az pipelines run --name "CI Build" --variables "debug=true" "verbosity=diagnostic"
```

### Logs and Artifacts

```powershell
# Get logs via REST (no direct CLI command for pipeline logs)
az devops invoke \
  --area pipelines \
  --resource logs \
  --route-parameters project=PROJECT pipelineId=PIPELINE_ID runId=RUN_ID \
  --api-version 7.0

# Download artifacts
az pipelines runs artifact download \
  --run-id RUN_ID \
  --artifact-name "drop" \
  --path ./artifacts

# View pipeline YAML definition
az pipelines show --name "CI Build" --output yaml
```

## Repos

### Branch Management

```powershell
# List branches
az repos ref list --repository REPO --filter heads/ --output table

# Create branch from main
az repos ref create \
  --name "refs/heads/feature/new-branch" \
  --repository REPO \
  --object-id $(az repos ref list --repository REPO --filter heads/main --query "[0].objectId" -o tsv)

# Delete branch
az repos ref delete \
  --name "refs/heads/feature/old-branch" \
  --repository REPO \
  --object-id COMMIT_SHA

# Lock/unlock branch
az repos ref lock --name "refs/heads/release/1.0" --repository REPO
az repos ref unlock --name "refs/heads/release/1.0" --repository REPO
```

### Branch Policies

```powershell
# List policies on a branch
az repos policy list --branch main --repository-id REPO_ID --output table

# Require minimum reviewers
az repos policy approver-count create \
  --branch main \
  --repository-id REPO_ID \
  --minimum-approver-count 2 \
  --creator-vote-counts false \
  --enabled true \
  --blocking true

# Require build validation
az repos policy build create \
  --branch main \
  --repository-id REPO_ID \
  --build-definition-id PIPELINE_ID \
  --display-name "CI Must Pass" \
  --enabled true \
  --blocking true \
  --queue-on-source-update-only true
```

## REST API via az devops invoke

For operations not covered by CLI commands:

```powershell
# Generic GET
az devops invoke \
  --area wit \
  --resource workitems \
  --route-parameters project=PROJECT id=12345 \
  --api-version 7.0

# Generic POST with body from file
az devops invoke \
  --area wit \
  --resource workitems \
  --route-parameters project=PROJECT \
  --api-version 7.0 \
  --http-method POST \
  --in-file body.json

# Get work item revisions (for cycle time)
az devops invoke \
  --area wit \
  --resource revisions \
  --route-parameters project=PROJECT workItemId=12345 \
  --api-version 7.0
```

## Output Formatting

```powershell
# Table (human readable)
az boards query --wiql "..." --output table

# JSON (for processing)
az boards query --wiql "..." --output json

# TSV (for scripting)
az boards work-item show --id 12345 --query "fields.\"System.Title\"" -o tsv

# JMESPath filtering
az boards query --wiql "..." --output json \
  --query "[].fields.{Id: 'System.Id', Title: 'System.Title', State: 'System.State'}"

# Pipe JSON to PowerShell
$items = az boards query --wiql "..." --output json | ConvertFrom-Json
$items | Where-Object { $_.fields.'System.State' -eq 'Active' } | Format-Table
```
