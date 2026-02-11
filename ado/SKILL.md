---
name: ado
description: Azure DevOps CLI (az devops) for work items, pull requests, pipelines, repos, and Kanban backlog management. Use when working with Azure DevOps for board queries, PR creation/review, pipeline debugging, or any ADO operations. Triggers on "az ado", "work item", "ADO", "azure devops", "backlog", "pipeline status", az boards, az repos, or az pipelines commands.
---

# ado — Azure DevOps CLI

Interact with Azure DevOps using the `az devops` CLI extension. Assumes `az login` authentication and org/project defaults are configured.

## Prerequisites

Verify auth and defaults before any operation:

```powershell
az account show --query "{name:name, user:user.name}" -o table
az devops configure --list
```

If defaults are missing:

```powershell
az devops configure --defaults organization=https://dev.azure.com/ORG project=PROJECT
```

## Quick Reference

```powershell
# Work Items
az boards work-item show --id ID
az boards work-item create --type "User Story" --title "Title"
az boards work-item update --id ID --state Active
az boards query --wiql "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'"

# Pull Requests
az repos pr create --title "Title" --work-items ID
az repos pr list --status active
az repos pr show --id ID
az repos pr set-vote --id ID --vote 10

# Pipelines
az pipelines run --name "pipeline-name"
az pipelines list --output table
az pipelines runs show --id RUN_ID
az pipelines runs list --pipeline-ids PIPELINE_ID --result failed

# Repos
az repos list --output table
az repos ref list --repository REPO
```

## State Transitions

### User Story Lifecycle

```
New → Ready to Review → Ready to Code → Active → Closed
```

| State | Meaning |
|-------|---------|
| New | Just created, not yet triaged |
| Ready to Review | Surfaces in planning meeting for discussion |
| Ready to Code | Planned, estimated (has story points), ready for dev |
| Active | Developer is actively working on it |
| Closed | Done |
| Removed | Deleted/cancelled |

### Feature & Epic Lifecycle

```
New → Active → Closed
```

### Transition Commands

```powershell
# Story through full lifecycle
az boards work-item update --id ID --state "Ready to Review"
az boards work-item update --id ID --state "Ready to Code"
az boards work-item update --id ID --state Active
az boards work-item update --id ID --state Closed
```

### Assign to Self

Resolve the current user dynamically — works for any logged-in user:

```powershell
$me = az account show --query "user.name" -o tsv
az boards work-item update --id ID --assigned-to $me
```

## Dev Flow

Standard work item → branch → PR → pipeline workflow.

### 1. Pick Up a Work Item

```powershell
# Find items ready to work on
az boards query --wiql "SELECT [System.Id], [System.Title], [System.State] `
  FROM WorkItems `
  WHERE [System.AssignedTo] = @Me `
  AND [System.State] = 'Ready to Code' `
  ORDER BY [Microsoft.VSTS.Common.Priority]" --output table

# Activate the item
az boards work-item update --id ID --state Active
```

### 2. Create a Branch

```powershell
git checkout -b feature/ID-short-description
```

### 3. Create a PR Linked to Work Item

```powershell
az repos pr create `
  --title "feat: description" `
  --description "Resolves AB#ID" `
  --work-items ID `
  --auto-complete true `
  --delete-source-branch true
```

The `--work-items` flag links the PR to the work item. Use `AB#ID` in description for additional linking.

### 4. Monitor Pipeline on PR

```powershell
# List runs for the PR's branch
az pipelines runs list --branch feature/ID-short-description --top 1 --output table

# Check run details
az pipelines runs show --id RUN_ID --output table
```

### 5. Complete PR

```powershell
az repos pr update --id PR_ID --status completed
```

Work item state transitions automatically if board rules are configured.

## Planning Flow

Create features and stories with parent-child hierarchy.

### Path Conventions

| Work Item Type | Area Path | Iteration Path |
|----------------|-----------|----------------|
| Epic | `Secure Cloud Access\Azure Encrypted Transport` | `Secure Cloud Access\Krypton` |
| Feature | `Secure Cloud Access\Azure Encrypted Transport\SWE` | `Secure Cloud Access\Krypton` |
| User Story | `Secure Cloud Access\Azure Encrypted Transport\SWE` | `Secure Cloud Access\Krypton` |
| Task | `Secure Cloud Access\Azure Encrypted Transport\SWE` | `Secure Cloud Access\Krypton` |
| Bug | `Secure Cloud Access\Azure Encrypted Transport\SWE` | `Secure Cloud Access\Krypton` |

### Descriptions and Acceptance Criteria

| Work Item Type | Description Field | Acceptance Criteria |
|----------------|-------------------|---------------------|
| Feature | `--description` (put AC here) | N/A — use description |
| User Story | `--description` (user story text) | `--fields "Microsoft.VSTS.Common.AcceptanceCriteria=..."` |

Both fields accept HTML. Use `<ul><li>` for bullet lists:

```powershell
# Feature — AC goes in description
az boards work-item update --id FEATURE_ID `
  --description "<h3>Acceptance Criteria</h3><ul><li>Criterion 1</li><li>Criterion 2</li></ul>"

# Story — description for the story, AC in its own field
az boards work-item update --id STORY_ID `
  --description "As a user, I want to..." `
  --fields "Microsoft.VSTS.Common.AcceptanceCriteria=<ul><li>Criterion 1</li><li>Criterion 2</li></ul>"
```

### Create a Feature Under an Epic

Create the feature, then link it to the parent epic:

```powershell
# Step 1: Create the feature
$featureId = az boards work-item create `
  --type Feature `
  --title "Feature title" `
  --description "Feature description" `
  --area "Secure Cloud Access\Azure Encrypted Transport\SWE" `
  --iteration "Secure Cloud Access\Krypton" `
  --query "id" -o tsv

# Step 2: Link to parent epic
az boards work-item relation add --id $featureId --relation-type parent --target-id EPIC_ID
```

### Create Stories Under a Feature

```powershell
# Step 1: Create the story
$storyId = az boards work-item create `
  --type "User Story" `
  --title "Story title" `
  --description "As a user, I want..." `
  --area "Secure Cloud Access\Azure Encrypted Transport\SWE" `
  --iteration "Secure Cloud Access\Krypton" `
  --query "id" -o tsv

# Step 2: Link to parent feature
az boards work-item relation add --id $storyId --relation-type parent --target-id FEATURE_ID
```

### Bulk Story Creation

Create multiple stories under a feature by chaining create + link:

```powershell
$featureId = FEATURE_ID
@("Story A", "Story B", "Story C") | ForEach-Object {
  $storyId = az boards work-item create --type "User Story" --title $_ `
    --area "Secure Cloud Access\Azure Encrypted Transport\SWE" `
    --iteration "Secure Cloud Access\Krypton" `
    --query "id" -o tsv
  az boards work-item relation add --id $storyId --relation-type parent --target-id $featureId
}
```

### Set Iteration and Area Paths

```powershell
az boards work-item update --id ID `
  --area "Project\Team\Area" `
  --iteration "Project\Sprint 1"
```

### Estimation (Story Points)

Story points use the first 10 Fibonacci numbers: **1, 1, 2, 3, 5, 8, 13, 21, 34, 55**

When asked to "estimate stories", assess complexity and set story points:

```powershell
az boards work-item update --id ID `
  --fields "Microsoft.VSTS.Scheduling.StoryPoints=5"
```

Bulk estimate multiple stories:

```powershell
# Hash of story ID → estimated points
$estimates = @{
  12345 = 3
  12346 = 8
  12347 = 5
}
$estimates.GetEnumerator() | ForEach-Object {
  az boards work-item update --id $_.Key --fields "Microsoft.VSTS.Scheduling.StoryPoints=$($_.Value)" --output table
}
```

| Points | Complexity |
|--------|------------|
| 1 | Trivial — config change, typo fix |
| 2 | Small — single file, well-understood change |
| 3 | Small-medium — a few files, straightforward |
| 5 | Medium — multiple files, some design needed |
| 8 | Medium-large — cross-component, some unknowns |
| 13 | Large — significant effort, multiple components |
| 21 | Very large — consider splitting |
| 34 | Epic-sized — must be split |
| 55 | Program-level — break into features |

## Backlog Management (Kanban)

All metrics use WIQL queries via `az boards query`.

### WIP — Items in Progress

```powershell
az boards query --wiql "SELECT [System.Id], [System.Title], [System.AssignedTo] `
  FROM WorkItems `
  WHERE [System.State] = 'Active' `
  AND [System.WorkItemType] = 'User Story' `
  ORDER BY [System.ChangedDate]" --output table
```

### Aging — Items Stale in a State

Find items stuck in Active for more than 7 days:

```powershell
az boards query --wiql "SELECT [System.Id], [System.Title], [System.ChangedDate] `
  FROM WorkItems `
  WHERE [System.State] = 'Active' `
  AND [System.ChangedDate] < @Today - 7 `
  AND [System.WorkItemType] = 'User Story'" --output table
```

### Throughput — Recently Completed

Items closed in the last 14 days:

```powershell
az boards query --wiql "SELECT [System.Id], [System.Title], [System.ChangedDate] `
  FROM WorkItems `
  WHERE [System.State] = 'Closed' `
  AND [System.ChangedDate] >= @Today - 14 `
  AND [System.WorkItemType] = 'User Story' `
  ORDER BY [System.ChangedDate] DESC" --output table
```

### State Distribution

Count items per state for board overview:

```powershell
$items = az boards query --wiql "SELECT [System.Id], [System.State] `
  FROM WorkItems `
  WHERE [System.WorkItemType] = 'User Story' `
  AND [System.State] <> 'Removed'" --output json | ConvertFrom-Json
$items | Group-Object { $_.fields.'System.State' } |
  Select-Object @{N='State';E={$_.Name}}, Count |
  Sort-Object Count -Descending | Format-Table
```

### Cycle Time

Query items with state change history (requires REST API for full history):

```powershell
az devops invoke `
  --area wit `
  --resource revisions `
  --route-parameters project=PROJECT workItemId=ID `
  --api-version 7.0
```

## Pipeline Debugging

### List Recent Runs

```powershell
az pipelines runs list --top 10 --output table
az pipelines runs list --pipeline-ids PIPELINE_ID --result failed --top 5 --output table
```

### View Run Details and Logs

```powershell
# Show run summary
az pipelines runs show --id RUN_ID --output table

# Get logs via REST (no direct CLI command for logs)
az devops invoke `
  --area pipelines `
  --resource logs `
  --route-parameters project=PROJECT pipelineId=PIPELINE_ID runId=RUN_ID `
  --api-version 7.0
```

### Trigger and Retry

```powershell
# Trigger a pipeline
az pipelines run --name "pipeline-name" --branch main

# Trigger with variables
az pipelines run --name "pipeline-name" --variables "env=staging" "deploy=true"
```

## References

For detailed command syntax and examples, consult:
- **`references/wiql-syntax.md`** — Full WIQL field names, operators, macros, link queries, and gotchas
- **`references/command-cookbook.md`** — Copy-paste command patterns for work items, PRs, pipelines, repos, bulk ops, and REST API

## Tips

- Always use `--output table` for readable terminal output, `--output json` for parsing
- Use `--query` with JMESPath to filter JSON output: `--query "[].{Id:id, Title:fields.\"System.Title\"}"`
- WIQL supports `@Me`, `@Today`, `@Today - N` macros
- Link PRs to work items with `AB#ID` in commit messages or PR descriptions
- Use `az devops wiki` commands for wiki operations
- Use `az boards iteration` and `az boards area` to manage team structure
