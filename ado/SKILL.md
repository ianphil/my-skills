---
name: ado
description: "Azure DevOps CLI (az ado). Use for work items, PRs, pipelines, and backlog management. Triggers on: az ado, ADO, azure devops, work item, backlog, az boards, az repos, az pipelines."
---

# ado - Azure DevOps CLI

Use `az devops` (plus `az boards`, `az repos`, `az pipelines`) from PowerShell. Assumes `az login` and org/project defaults.

## Configuration
If `ado\config.json` is missing, ask:
1. What is your ADO organization URL? (e.g., `https://dev.azure.com/myorg`)
2. What is your project name?
3. What area path should Epics use?
4. What area path should Features/Stories/Tasks/Bugs use?
5. What iteration path should work items use?

Save to `ado\config.json` (gitignored). Config shape:
```json
{
  "organization": "https://dev.azure.com/ORG",
  "project": "PROJECT",
  "areaPaths": {
    "epic": "Project\\Team",
    "feature": "Project\\Team\\SubTeam",
    "story": "Project\\Team\\SubTeam",
    "task": "Project\\Team\\SubTeam",
    "bug": "Project\\Team\\SubTeam"
  },
  "iterationPath": "Project\\Iteration",
  "storyPointScale": [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
}
```

Load config:
```powershell
$config = Get-Content ".\ado\config.json" | ConvertFrom-Json
```

## Prerequisites
Verify auth and defaults:
```powershell
az account show --query "{name:name, user:user.name}" -o table
az devops configure --list
```

If defaults are missing:
```powershell
az devops configure --defaults organization=$config.organization project=$config.project
```

## Rules
- Always use PowerShell for scripting and JSON; do not pipe to python/node.
- Use `--query` JMESPath on `az` commands to filter JSON before PowerShell when possible.
- For any multi-step operation, read the matching section below first; never guess `az` flags or parameters.

## State Transitions
### User Story lifecycle
`New -> Ready to Review -> Ready to Code -> Active -> Closed`

| State | Meaning |
|-------|---------|
| New | Just created, not triaged |
| Ready to Review | Discuss in planning |
| Ready to Code | Planned and estimated |
| Active | In progress |
| Closed | Done |
| Removed | Deleted/cancelled |

### Feature and Epic lifecycle
`New -> Active -> Closed`

### Transition commands
```powershell
az boards work-item update --id ID --state "Ready to Review"
az boards work-item update --id ID --state "Ready to Code"
az boards work-item update --id ID --state Active
az boards work-item update --id ID --state Closed
```

## Quick Reference
Essential commands. For multi-step workflows, read the matching section in "Section Router" first.
```powershell
# Show a work item
az boards work-item show --id ID --output table

# Show with relations (children, parent, related)
az boards work-item show --id ID --expand relations --output json

# Get child IDs from a parent (e.g., features under an epic)
$json = az boards work-item show --id PARENT_ID --expand relations --output json | ConvertFrom-Json
$childIds = $json.relations | Where-Object { $_.attributes.name -eq 'Child' } | ForEach-Object { $_.url -replace '.*/', '' }

# Show multiple work items (loop - there is no --ids flag)
$childIds | ForEach-Object { az boards work-item show --id $_ --output json } | ForEach-Object { $_ | ConvertFrom-Json } | Select-Object id, @{N='Type';E={$_.fields.'System.WorkItemType'}}, @{N='Title';E={$_.fields.'System.Title'}}, @{N='State';E={$_.fields.'System.State'}} | Format-Table

# Query work items with WIQL
az boards query --wiql "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.WorkItemType] = 'User Story' AND [System.State] = 'Active'" --output table

# Create a work item
az boards work-item create --type "User Story" --title "Title" --area $config.areaPaths.story --iteration $config.iterationPath

# Link child to parent (no --parent flag exists)
az boards work-item relation add --id CHILD_ID --relation-type parent --target-id PARENT_ID

# Update state
az boards work-item update --id ID --state Active

# Create a PR linked to work item
az repos pr create --title "feat: description" --work-items ID --auto-complete true --delete-source-branch true

# List active PRs
az repos pr list --status active --output table

# List pipeline runs
az pipelines runs list --top 5 --output table
```

## Section Router
| User intent | Section | Read before |
|-------------|---------|-------------|
| Pick up work items, create branches, make PRs, monitor builds | Dev Flow | Any PR or branch workflow |
| Create features/stories, hierarchy, area paths, estimation | Planning Flow | Creating or linking work items |
| WIP, aging, throughput, cycle time, Kanban health | Backlog Management | Any backlog query or metric |
| Pipeline status, failed builds, logs, triggers | Pipeline Debugging | Any pipeline operation |
| WIQL field names, operators, macros, quoting | WIQL Reference | Writing any WIQL query |
| CLI command patterns, bulk ops, REST API, output formatting | Command Cookbook | Bulk operations or REST API calls |
| Board columns, WIP limits, Kanban column queries | Board Columns API | Any board column query |

## Troubleshooting
| Problem | Fix |
|---------|-----|
| `az account show` fails | Re-run `az login` - token expired |
| Empty query results | Check area path spelling; for `FROM WorkItemLinks` use REST API instead |
| `charmap` encoding error | Use `az devops invoke` not `az rest`; set `$env:PYTHONIOENCODING = "utf-8"` |
| Defaults not set | Run `az devops configure --defaults organization=$config.organization project=$config.project` |
| Permission denied on work items | Verify area path permissions in ADO project settings |
| WIQL syntax error | Check quoting; see WIQL Reference |

## Additional Tips
- Use `--output table` for readable output, `--output json` for parsing
- Use `--query` with JMESPath to filter JSON: `--query "[].{Id:id, Title:fields.\"System.Title\"}"`
- WIQL supports `@Me`, `@Today`, `@Today - N` macros
- Link PRs to work items with `AB#ID` in commits or PR descriptions
- Use `az devops wiki` for wiki operations
- Use `az boards iteration` and `az boards area` to manage team structure

## Dev Flow - Work Item -> Branch -> PR -> Merge
Use for picking up work items, creating branches, making PRs, or monitoring PR pipelines.

### 1. Pick up a work item
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

### 2. Create a branch
```powershell
git checkout -b feature/ID-short-description
```

### 3. Create a PR linked to work item
```powershell
az repos pr create `
  --title "feat: description" `
  --description "Resolves AB#ID" `
  --work-items ID `
  --auto-complete true `
  --delete-source-branch true
```

The `--work-items` flag links the PR. Use `AB#ID` in description for extra linking.

### 4. Monitor pipeline on PR
```powershell
# List runs for the PR branch
az pipelines runs list --branch feature/ID-short-description --top 1 --output table

# Check run details
az pipelines runs show --id RUN_ID --output table
```

### 5. Complete PR
```powershell
az repos pr update --id PR_ID --status completed
```

Work item state transitions automatically if board rules are configured.

### Assign to self
```powershell
$me = az account show --query "user.name" -o tsv
az boards work-item update --id ID --assigned-to $me
```

## Planning Flow - Features, Stories, Hierarchy and Estimation
Assumes `$config` loaded from `.\ado\config.json`.

### Path conventions
| Work Item Type | Area Path (config key) | Iteration Path (config key) |
|---------------|------------------------|-----------------------------|
| Epic | `areaPaths.epic` | `iterationPath` |
| Feature | `areaPaths.feature` | `iterationPath` |
| User Story | `areaPaths.story` | `iterationPath` |
| Task | `areaPaths.task` | `iterationPath` |
| Bug | `areaPaths.bug` | `iterationPath` |

### Descriptions and acceptance criteria
| Work Item Type | Description Field | Acceptance Criteria |
|---------------|-------------------|---------------------|
| Feature | `--description` (put AC here) | N/A - use description |
| User Story | `--description` (user story text) | `--fields "Microsoft.VSTS.Common.AcceptanceCriteria=..."` |

Both fields accept HTML. Use `<ul><li>` for bullet lists:
```powershell
# Feature - AC goes in description
az boards work-item update --id FEATURE_ID `
  --description "<h3>Acceptance Criteria</h3><ul><li>Criterion 1</li><li>Criterion 2</li></ul>"

# Story - description for story, AC in its own field
az boards work-item update --id STORY_ID `
  --description "As a user, I want to..." `
  --fields "Microsoft.VSTS.Common.AcceptanceCriteria=<ul><li>Criterion 1</li><li>Criterion 2</li></ul>"
```

### Create a Feature under an Epic
```powershell
$featureId = az boards work-item create `
  --type Feature `
  --title "Feature title" `
  --description "Feature description" `
  --area $config.areaPaths.feature `
  --iteration $config.iterationPath `
  --query "id" -o tsv

az boards work-item relation add --id $featureId --relation-type parent --target-id EPIC_ID
```

### Create Stories under a Feature
```powershell
$storyId = az boards work-item create `
  --type "User Story" `
  --title "Story title" `
  --description "As a user, I want..." `
  --area $config.areaPaths.story `
  --iteration $config.iterationPath `
  --query "id" -o tsv

az boards work-item relation add --id $storyId --relation-type parent --target-id FEATURE_ID
```

### Bulk story creation
```powershell
$featureId = FEATURE_ID
@("Story A", "Story B", "Story C") | ForEach-Object {
  $storyId = az boards work-item create --type "User Story" --title $_ `
    --area $config.areaPaths.story `
    --iteration $config.iterationPath `
    --query "id" -o tsv
  az boards work-item relation add --id $storyId --relation-type parent --target-id $featureId
}
```

### Set iteration and area paths
```powershell
az boards work-item update --id ID `
  --area $config.areaPaths.story `
  --iteration $config.iterationPath
```

### Estimation (Story Points)
Story points use the scale from `config.json` (default: first 10 Fibonacci numbers).
```powershell
az boards work-item update --id ID `
  --fields "Microsoft.VSTS.Scheduling.StoryPoints=5"
```

### Bulk estimate stories
```powershell
$estimates = @{
  12345 = 3
  12346 = 8
  12347 = 5
}
$estimates.GetEnumerator() | ForEach-Object {
  az boards work-item update --id $_.Key `
    --fields "Microsoft.VSTS.Scheduling.StoryPoints=$($_.Value)" --output table
}
```

### Complexity guide
| Points | Complexity |
|--------|------------|
| 1 | Trivial - config change, typo fix |
| 2 | Small - single file, well-understood change |
| 3 | Small-medium - a few files, straightforward |
| 5 | Medium - multiple files, some design needed |
| 8 | Medium-large - cross-component, some unknowns |
| 13 | Large - significant effort, multiple components |
| 21 | Very large - consider splitting |
| 34 | Epic-sized - must be split |
| 55 | Program-level - break into features |

## Backlog Management - Kanban Metrics and Queries
For WIQL syntax, see WIQL Reference. For board columns and WIP limits, see Board Columns API.

### WIP - Items in progress
```powershell
az boards query --wiql "SELECT [System.Id], [System.Title], [System.AssignedTo] `
  FROM WorkItems `
  WHERE [System.State] = 'Active' `
  AND [System.WorkItemType] = 'User Story' `
  ORDER BY [System.ChangedDate]" --output table
```

### Aging - Items stale in a state
Find items stuck in Active for more than 7 days:
```powershell
az boards query --wiql "SELECT [System.Id], [System.Title], [System.ChangedDate] `
  FROM WorkItems `
  WHERE [System.State] = 'Active' `
  AND [System.ChangedDate] < @Today - 7 `
  AND [System.WorkItemType] = 'User Story'" --output table
```

### Throughput - Recently completed
Items closed in the last 14 days:
```powershell
az boards query --wiql "SELECT [System.Id], [System.Title], [System.ChangedDate] `
  FROM WorkItems `
  WHERE [System.State] = 'Closed' `
  AND [System.ChangedDate] >= @Today - 14 `
  AND [System.WorkItemType] = 'User Story' `
  ORDER BY [System.ChangedDate] DESC" --output table
```

### State distribution
Count items per state:
```powershell
$items = az boards query --wiql "SELECT [System.Id], [System.State] `
  FROM WorkItems `
  WHERE [System.WorkItemType] = 'User Story' `
  AND [System.State] <> 'Removed'" --output json | ConvertFrom-Json
$items | Group-Object { $_.fields.'System.State' } |
  Select-Object @{N='State';E={$_.Name}}, Count |
  Sort-Object Count -Descending | Format-Table
```

### Cycle time
Query item revision history (REST):
```powershell
az devops invoke `
  --area wit `
  --resource revisions `
  --route-parameters project=$config.project workItemId=ID `
  --api-version 7.0
```

## Pipeline Debugging - Runs, Logs and Triggers
Use for pipeline status, failed builds, logs, triggering pipelines, or retrying runs.

### List recent runs
```powershell
az pipelines runs list --top 10 --output table
az pipelines runs list --pipeline-ids PIPELINE_ID --result failed --top 5 --output table
```

### View run details and logs
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

### Trigger and retry
```powershell
# Trigger a pipeline
az pipelines run --name "pipeline-name" --branch main

# Trigger with variables
az pipelines run --name "pipeline-name" --variables "env=staging" "deploy=true"
```

### Download artifacts
```powershell
az pipelines runs artifact download `
  --run-id RUN_ID `
  --artifact-name "drop" `
  --path ./artifacts
```

### View pipeline definition
```powershell
az pipelines show --name "CI Build" --output yaml
```

## Command Cookbook
Use for CLI patterns, bulk ops, REST API calls, and output formatting.

### Work Items
#### Create
```powershell
# User Story
az boards work-item create `
  --type "User Story" `
  --title "Implement login page" `
  --description "As a user, I want to log in so I can access my account." `
  --assigned-to "user@example.com" `
  --area $config.areaPaths.story `
  --iteration $config.iterationPath

# Bug
az boards work-item create `
  --type Bug `
  --title "Login button unresponsive on mobile" `
  --description "<p>Steps to reproduce:</p><ol><li>Open mobile browser</li><li>Tap login</li></ol>" `
  --assigned-to "user@example.com"

# Task under a Story (create then link)
$taskId = az boards work-item create `
  --type Task `
  --title "Write unit tests for auth module" `
  --query "id" -o tsv
az boards work-item relation add --id $taskId --relation-type parent --target-id STORY_ID
```

For hierarchy creation, see Planning Flow.

#### Parent-Child Linking
There is no `--parent` flag on `az boards work-item create`. Use `relation add` after creation:
```powershell
# Link child to parent
az boards work-item relation add --id CHILD_ID --relation-type parent --target-id PARENT_ID

# Link multiple children to same parent
az boards work-item relation add --id PARENT_ID --relation-type child --target-id CHILD1,CHILD2,CHILD3

# View relations on a work item
az boards work-item relation show --id 12345 --output table
```

#### Read
```powershell
# Show single item
az boards work-item show --id 12345 --output table

# Show with all relations/links
az boards work-item show --id 12345 --expand relations

# Note: --fields and --expand cannot be used together
```

#### Update
```powershell
# Change state
az boards work-item update --id 12345 --state Active
az boards work-item update --id 12345 --state Closed

# Reassign
az boards work-item update --id 12345 --assigned-to "other@example.com"

# Update title and description
az boards work-item update --id 12345 `
  --title "Updated title" `
  --description "Updated description"

# Add tags
az boards work-item update --id 12345 --fields "System.Tags=api,backend,priority"

# Move to different area/iteration
az boards work-item update --id 12345 `
  --area $config.areaPaths.story `
  --iteration $config.iterationPath

# Update custom fields using --fields
az boards work-item update --id 12345 `
  --fields "Microsoft.VSTS.Scheduling.StoryPoints=5"
```

#### Delete
```powershell
# Delete (moves to recycle bin)
az boards work-item delete --id 12345 --yes

# Permanently destroy (cannot undo)
az boards work-item delete --id 12345 --destroy --yes
```

#### Bulk operations (PowerShell)
```powershell
# Bulk close items by query
$ids = az boards query --wiql "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Resolved'" --output json | ConvertFrom-Json
$ids | ForEach-Object { az boards work-item update --id $_.id --state Closed }

# Bulk assign
@(100, 101, 102) | ForEach-Object {
  az boards work-item update --id $_ --assigned-to "dev@example.com"
}
```

### Pull Requests
#### Create
```powershell
# Basic PR
az repos pr create `
  --title "feat: add user authentication" `
  --description "Implements OAuth2 login flow. Resolves AB#12345"

# PR with full options
az repos pr create `
  --title "feat: add user authentication" `
  --description "Implements OAuth2 login flow" `
  --source-branch feature/12345-auth `
  --target-branch main `
  --work-items 12345 12346 `
  --reviewers "reviewer@example.com" `
  --auto-complete true `
  --delete-source-branch true `
  --squash true

# Draft PR
az repos pr create `
  --title "WIP: refactoring auth module" `
  --draft
```

#### Review and manage
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
az devops invoke `
  --area git `
  --resource pullRequestThreads `
  --route-parameters project=$config.project repositoryId=REPO pullRequestId=42 `
  --api-version 7.0 `
  --http-method POST `
  --in-file comment.json
```

#### PR work item linking
```powershell
# Link work items when creating PR
az repos pr create --title "fix: resolve bug" --work-items 12345 12346

# Add work item link to existing PR
az repos pr work-item add --id 42 --work-items 12345

# List linked work items
az repos pr work-item list --id 42 --output table
```

### Repos
#### Branch management
```powershell
# List branches
az repos ref list --repository REPO --filter heads/ --output table

# Create branch from main
az repos ref create `
  --name "refs/heads/feature/new-branch" `
  --repository REPO `
  --object-id $(az repos ref list --repository REPO --filter heads/main --query "[0].objectId" -o tsv)

# Delete branch
az repos ref delete `
  --name "refs/heads/feature/old-branch" `
  --repository REPO `
  --object-id COMMIT_SHA

# Lock/unlock branch
az repos ref lock --name "refs/heads/release/1.0" --repository REPO
az repos ref unlock --name "refs/heads/release/1.0" --repository REPO
```

#### Branch policies
```powershell
# List policies on a branch
az repos policy list --branch main --repository-id REPO_ID --output table

# Require minimum reviewers
az repos policy approver-count create `
  --branch main `
  --repository-id REPO_ID `
  --minimum-approver-count 2 `
  --creator-vote-counts false `
  --enabled true `
  --blocking true

# Require build validation
az repos policy build create `
  --branch main `
  --repository-id REPO_ID `
  --build-definition-id PIPELINE_ID `
  --display-name "CI Must Pass" `
  --enabled true `
  --blocking true `
  --queue-on-source-update-only true
```

### REST API via az devops invoke
```powershell
# Generic GET
az devops invoke `
  --area wit `
  --resource workitems `
  --route-parameters project=$config.project id=12345 `
  --api-version 7.0

# Generic POST with body from file
az devops invoke `
  --area wit `
  --resource workitems `
  --route-parameters project=$config.project `
  --api-version 7.0 `
  --http-method POST `
  --in-file body.json

# Get work item revisions (for cycle time)
az devops invoke `
  --area wit `
  --resource revisions `
  --route-parameters project=$config.project workItemId=12345 `
  --api-version 7.0
```

### Output formatting
```powershell
# Table (human readable)
az boards query --wiql "..." --output table

# JSON (for processing)
az boards query --wiql "..." --output json

# TSV (for scripting)
az boards work-item show --id 12345 --query "fields.\"System.Title\"" -o tsv

# JMESPath filtering
az boards query --wiql "..." --output json `
  --query "[].fields.{Id: 'System.Id', Title: 'System.Title', State: 'System.State'}"

# Pipe JSON to PowerShell
$items = az boards query --wiql "..." --output json | ConvertFrom-Json
$items | Where-Object { $_.fields.'System.State' -eq 'Active' } | Format-Table
```

## Board Columns API (REST)
Use for board columns, WIP limits, or Kanban column configuration. For board-level metrics, see Backlog Management.

The `az boards` CLI does not expose board column configuration directly. Use `az devops invoke`.

### Step 1: List boards for a team
Get board IDs for the team:
```powershell
az devops invoke `
  --area work `
  --resource boards `
  --route-parameters project=$config.project team="{TEAM_NAME}" `
  --api-version 7.0 --output json
```

Returns board metadata with IDs:
```json
{
  "count": 5,
  "value": [
    { "id": "...", "name": "Stories" },
    { "id": "...", "name": "Epics" },
    { "id": "...", "name": "Features" }
  ]
}
```

### Step 2: Fetch columns for a specific board
Pass the board `id` to get column details including WIP limits:
```powershell
$boardId = "{BOARD_ID}"

$result = az devops invoke `
  --area work `
  --resource boards `
  --route-parameters project=$config.project `
    team="{TEAM_NAME}" `
    id=$boardId `
  --api-version 7.0 --output json

$board = $result | ConvertFrom-Json
foreach ($col in $board.columns) {
    $wip = if ($col.itemLimit -and $col.itemLimit -gt 0) { $col.itemLimit } else { "none" }
    Write-Host ("{0,-30} WIP Limit: {1}" -f $col.name, $wip)
}
```

### Gotchas
- Do NOT use `az rest` for this endpoint; responses can include Unicode (infinity symbol U+221E) that triggers Windows `charmap` errors.
- Use `az devops invoke` instead, which handles encoding correctly.
- The list endpoint (`--resource boards` without `id`) returns metadata only; pass the board `id` to get column details.
- Set `$env:PYTHONIOENCODING = "utf-8"` as a safety net for encoding issues.

### Step 3: Query work items by board column
Board columns like "PR", "Testing", "Deployment" may share the same underlying state (e.g., "Active"). Use `System.BoardColumn` for precise column queries:
```powershell
az boards query --wiql "SELECT [System.Id], [System.Title], [System.AssignedTo], [System.BoardColumn] `
  FROM WorkItems `
  WHERE [System.WorkItemType] = 'User Story' `
  AND [System.AreaPath] UNDER $config.areaPaths.story `
  AND [System.BoardColumn] = 'PR' `
  AND [System.State] <> 'Removed' `
  ORDER BY [System.ChangedDate] DESC" --output table
```

### Available board column values
These match the column names from Step 2. For the Stories board:
| Board Column | Underlying State | WIP Limit |
|-------------|------------------|-----------|
| New | New | none |
| Ready | Ready to Code | none |
| Active | Active | 8 |
| PR | Active | 5 |
| Testing | Active | 3 |
| Deployment | Active | 3 |
| Closed | Closed | none |

### Key insight
Multiple board columns can map to the same ADO state (e.g., "PR", "Testing", "Deployment" all map to "Active"). Querying by `System.State = 'Active'` returns items across all those columns. Use `System.BoardColumn` for column-level precision.

### Check WIP compliance
Compare column item count against WIP limit:
```powershell
$columns = @("Active", "PR", "Testing", "Deployment")
foreach ($col in $columns) {
    $items = az boards query --wiql "SELECT [System.Id] FROM WorkItems `
      WHERE [System.WorkItemType] = 'User Story' `
      AND [System.AreaPath] UNDER $config.areaPaths.story `
      AND [System.BoardColumn] = '$col' `
      AND [System.State] <> 'Removed'" --output json | ConvertFrom-Json
    Write-Host "$col : $($items.Count) items"
}
```

### API reference
- [Boards - Get](https://learn.microsoft.com/en-us/rest/api/azure/devops/work/boards/get) - `GET {org}/{project}/{team}/_apis/work/boards/{board}?api-version=7.0`
- [Boards - List](https://learn.microsoft.com/en-us/rest/api/azure/devops/work/boards/list) - `GET {org}/{project}/{team}/_apis/work/boards?api-version=7.0`
- [WIQL BoardColumn](https://learn.microsoft.com/en-us/azure/devops/boards/queries/query-by-workflow-changes) - `System.BoardColumn` field reference

## WIQL Reference
Use for field names, operators, macros, quoting rules, or link query syntax. WIQL is used with `az boards query --wiql "..."`.

### Clause structure
```sql
SELECT [Field1], [Field2]
FROM WorkItems                    -- or WorkItemLinks for link queries
WHERE [Condition1] AND [Condition2]
ORDER BY [Field] ASC|DESC
ASOF 'YYYY-MM-DD'                -- optional: historical point-in-time query
```

- `SELECT *` is not supported; list each field explicitly.
- Use `FROM WorkItems` for flat queries, `FROM WorkItemLinks` for link/hierarchy queries.
- `ASOF` must be the last clause and is not compatible with link queries.

### Field names
Always use bracket syntax: `[System.FieldName]`.

#### Common fields
| Field | Description |
|-------|-------------|
| `[System.Id]` | Work item ID |
| `[System.Title]` | Title (single-line text) |
| `[System.State]` | Current state (New, Active, Resolved, Closed, Removed) |
| `[System.WorkItemType]` | Type (Epic, Feature, User Story, Task, Bug) |
| `[System.AssignedTo]` | Assigned person (identity field) |
| `[System.CreatedDate]` | Creation date |
| `[System.ChangedDate]` | Last modified date |
| `[System.CreatedBy]` | Creator (identity field) |
| `[System.Tags]` | Tags (comma-separated string) |
| `[System.AreaPath]` | Area path (tree path) |
| `[System.IterationPath]` | Iteration path (tree path) |
| `[System.Description]` | Description (HTML/rich-text) |
| `[System.TeamProject]` | Project name |
| `[System.BoardColumn]` | Current Kanban column |
| `[System.BoardColumnDone]` | Whether in done split of column |

#### Priority and effort
| Field | Description |
|-------|-------------|
| `[Microsoft.VSTS.Common.Priority]` | Priority (1=Critical, 2=High, 3=Medium, 4=Low) |
| `[Microsoft.VSTS.Common.Severity]` | Bug severity |
| `[Microsoft.VSTS.Scheduling.StoryPoints]` | Story points |
| `[Microsoft.VSTS.Scheduling.Effort]` | Effort |
| `[Microsoft.VSTS.Common.ValueArea]` | Business or Architectural |

#### Dates and history
| Field | Description |
|-------|-------------|
| `[Microsoft.VSTS.Common.ClosedDate]` | Date item was closed |
| `[Microsoft.VSTS.Common.ResolvedDate]` | Date item was resolved |
| `[Microsoft.VSTS.Common.ActivatedDate]` | Date item was activated |
| `[Microsoft.VSTS.Common.StateChangeDate]` | Last state change date |

### Operators
#### Comparison
| Operator | Field Types | Example |
|----------|-------------|---------|
| `=` | All | `[System.State] = 'Active'` |
| `<>` | All | `[System.State] <> 'Removed'` |
| `>`, `<`, `>=`, `<=` | Number, Date | `[Microsoft.VSTS.Common.Priority] <= 2` |
| `IN` | String, Number | `[System.State] IN ('New', 'Active')` |
| `NOT IN` | String, Number | `[System.State] NOT IN ('Closed', 'Removed')` |

#### Text search
| Operator | Field Types | Indexed | Example |
|----------|-------------|---------|---------|
| `CONTAINS` | String (single-line) | No | `[System.Title] CONTAINS 'auth'` |
| `NOT CONTAINS` | String (single-line) | No | `[System.Title] NOT CONTAINS 'test'` |
| `CONTAINS WORDS` | String, PlainText, HTML | Yes | `[System.Description] CONTAINS WORDS 'authentication failed'` |
| `NOT CONTAINS WORDS` | String, PlainText, HTML | Yes | `[System.Description] NOT CONTAINS WORDS 'obsolete'` |

Notes:
- `CONTAINS` is a slow unindexed substring scan.
- `CONTAINS WORDS` is indexed, faster, and supports stemming.
- Use `CONTAINS WORDS` for Description/repro steps; use `CONTAINS` for Title/Tags.
- `CONTAINS WORDS` limit: 100 characters max in search phrase.

#### Path operators
| Operator | Field Types | Example |
|----------|-------------|---------|
| `UNDER` | AreaPath, IterationPath | `[System.AreaPath] UNDER '{AREA_PATH}'` |
| `NOT UNDER` | AreaPath, IterationPath | `[System.IterationPath] NOT UNDER '{ITERATION_PATH}'` |

`UNDER` matches the path itself and all children beneath it.

#### Identity operators
| Operator | Field Types | Example |
|----------|-------------|---------|
| `IN GROUP` | Identity fields | `[System.AssignedTo] IN GROUP 'My Team'` |
| `NOT IN GROUP` | Identity fields | `[System.AssignedTo] NOT IN GROUP 'Contractors'` |

`IN GROUP` checks membership in an ADO security group or team.

#### Historical operators
| Operator | Field Types | Example |
|----------|-------------|---------|
| `WAS EVER` | Identity, State, picklist | `[System.AssignedTo] WAS EVER 'alice@example.com'` |
| `EVER` | State | `[System.State] EVER 'Active'` |

`WAS EVER` checks if a field ever had a value at any point in history.

#### Null checks
| Operator | Example |
|----------|---------|
| `= ''` | `[System.AssignedTo] = ''` (unassigned) |
| `<> ''` | `[System.AssignedTo] <> ''` (assigned) |

### Macros
| Macro | Description |
|-------|-------------|
| `@Me` | Current authenticated user |
| `@Today` | Today's date (midnight, server timezone) |
| `@Today - N` | N days ago |
| `@Today + N` | N days from now |
| `@Project` | Current project name |
| `@CurrentIteration` | Current team iteration (requires team context) |
| `@CurrentIteration + N` | N iterations ahead |
| `@CurrentIteration - N` | N iterations back |

Warning: `@CurrentIteration` requires team context and may not resolve in all CLI contexts. Use explicit iteration paths when querying via `az boards query`.

### Query patterns
#### Basic SELECT
```sql
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.WorkItemType] = 'User Story'
  AND [System.State] = 'Active'
ORDER BY [Microsoft.VSTS.Common.Priority]
```

#### Historical query (ASOF)
```sql
SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] = 'User Story'
  AND [System.State] = 'Active'
ORDER BY [System.ChangedDate] DESC
ASOF '2025-01-15'
```

- Date format: `'YYYY-MM-DD'` (ISO 8601 recommended).
- Cannot be used with `FROM WorkItemLinks` (flat queries only).
- Returns work item data as it existed on that date.

#### Hierarchical (Parent-Child)
WARNING: `az boards query` silently returns empty results for `FROM WorkItemLinks`. Use REST API via `az devops invoke` instead:
```powershell
# Save WIQL to a temp file (required for POST body)
$body = '{"query": "SELECT [System.Id], [System.Title] FROM WorkItemLinks WHERE (Source.[System.Id] = 12345) AND ([System.Links.LinkType] = ''System.LinkTypes.Hierarchy-Forward'') MODE (MustContain)"}'
$body | Out-File -Encoding utf8 wiql-query.json

az devops invoke `
  --area wit `
  --resource wiql `
  --http-method POST `
  --api-version 7.0 `
  --route-parameters project=$config.project `
  --in-file wiql-query.json `
  --output json

Remove-Item wiql-query.json
```

The response contains `workItemRelations` with source/target ID pairs; fetch full work item details separately.

For flat queries that find children without link syntax, use:
```sql
SELECT [System.Id], [System.Title], [System.WorkItemType]
FROM WorkItems
WHERE [System.WorkItemType] = 'Feature'
  AND [System.AreaPath] UNDER '{AREA_PATH}'
```

Or use `az boards work-item relation show --id PARENT_ID` to list children directly.

#### Link query WIQL syntax (REST API)
Find all stories under all features:
```sql
SELECT [System.Id], [System.Title], [System.WorkItemType]
FROM WorkItemLinks
WHERE (Source.[System.WorkItemType] = 'Feature')
  AND ([System.Links.LinkType] = 'System.LinkTypes.Hierarchy-Forward')
  AND (Target.[System.WorkItemType] = 'User Story')
MODE (Recursive)
```

Find all descendants of a specific work item:
```sql
SELECT [System.Id], [System.Title], [System.WorkItemType]
FROM WorkItemLinks
WHERE (Source.[System.Id] = 12345)
  AND ([System.Links.LinkType] = 'System.LinkTypes.Hierarchy-Forward')
MODE (Recursive, MustContain)
```

#### Related links
```sql
SELECT [System.Id], [System.Title]
FROM WorkItemLinks
WHERE (Source.[System.Id] = 12345)
  AND ([System.Links.LinkType] = 'System.LinkTypes.Related-Forward')
MODE (MustContain)
```

#### Link query modes
| Mode | Behavior |
|------|----------|
| `MustContain` | Only return items that have matching links |
| `MayContain` | Return items regardless of whether they have matching links |
| `DoesNotContain` | Only return items that do NOT have matching links |
| `Recursive` | Traverse hierarchy recursively (all descendants) |

Modes can be combined: `MODE (Recursive, MustContain)`

#### Common link types
| Link Type | Description |
|-----------|-------------|
| `System.LinkTypes.Hierarchy-Forward` | Parent -> Child |
| `System.LinkTypes.Hierarchy-Reverse` | Child -> Parent |
| `System.LinkTypes.Related-Forward` | Related item |
| `System.LinkTypes.Dependency-Forward` | Successor (depends on) |
| `System.LinkTypes.Dependency-Reverse` | Predecessor |

List all link types in your org: `az boards work-item relation list-type --output table`

### az boards query usage
```powershell
# Flat query
az boards query --wiql "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.State] = 'Active'" --output table

# Output as JSON for processing
az boards query --wiql "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'" --output json

# Query by saved query ID (from ADO web portal)
az boards query --id QUERY_ID --output table

# Query with org/project override
az boards query --wiql "..." --org https://dev.azure.com/ORG --project PROJECT
```

### PowerShell quoting for WIQL
Rules:
1. Outer quotes: use double quotes `"` to wrap the `--wiql` value.
2. Inner string values: use single quotes inside WIQL.
3. Escape single quotes in values by doubling them.

Examples:
```powershell
# Standard query - double outside, single inside
az boards query --wiql "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'" --output table

# Value containing a single quote (O'Brien)
az boards query --wiql "SELECT [System.Id] FROM WorkItems WHERE [System.Title] CONTAINS 'O''Brien'"

# Multi-line query in PowerShell (use backtick for continuation)
az boards query --wiql "SELECT [System.Id], [System.Title], [System.State] `
  FROM WorkItems `
  WHERE [System.WorkItemType] = 'User Story' `
  AND [System.State] = 'Active' `
  AND [System.AreaPath] UNDER '{AREA_PATH}' `
  ORDER BY [Microsoft.VSTS.Common.Priority]" --output table

# Store WIQL in a variable for complex queries
$wiql = @"
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.WorkItemType] = 'User Story'
  AND [System.State] IN ('New', 'Active')
  AND [System.AreaPath] UNDER '{AREA_PATH}'
ORDER BY [System.ChangedDate] DESC
"@
az boards query --wiql $wiql --output table
```

Tip: For complex queries, the here-string (`@"..."@`) approach avoids quoting issues.

### Gotchas
#### Quoting and syntax
- String values use single quotes inside WIQL: `'Active'` not `"Active"`.
- To embed a literal single quote, double it: `'O''Brien'`.
- Field names are case-insensitive but bracket syntax `[...]` is required.
- `SELECT *` is not supported - always list fields explicitly.

#### Operators
- `CONTAINS` is a slow unindexed substring scan - avoid on large result sets.
- `CONTAINS WORDS` is fast indexed full-text - prefer for Description/repro steps.
- `CONTAINS WORDS` supports stemming ("run" matches "running").
- `UNDER` matches the path itself and all children beneath it.
- `WAS EVER` works on identity and picklist fields, not just `[System.State]`.

#### Dates
- Date comparisons use server timezone, not local timezone.
- No date arithmetic between fields; compute date diffs outside WIQL.
- `@Today` resolves to midnight server time.

#### Limits and restrictions
- Maximum 20,000 results per query.
- `ORDER BY` supports one field, ascending (default) or `DESC`.
- `ASOF` is not compatible with `FROM WorkItemLinks` (flat queries only).
- `az boards query` silently returns empty for `FROM WorkItemLinks` - use REST API via `az devops invoke`.
- `@CurrentIteration` requires team context and may fail in CLI without team scope.
- REST API WIQL endpoint returns only IDs; a second call is needed to fetch field values.
- Area/iteration paths should not contain quotes (no escape mechanism).
- `--fields` and `--expand` cannot be used together on `az boards work-item show`.
