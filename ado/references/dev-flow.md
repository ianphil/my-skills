# Dev Flow — Work Item → Branch → PR → Merge

> Load this file when the user asks about picking up work items, creating branches, making PRs, or monitoring pipelines for a PR.

## 1. Pick Up a Work Item

```powershell
$config = Get-Content "$PSScriptRoot\..\config.json" | ConvertFrom-Json

# Find items ready to work on
az boards query --wiql "SELECT [System.Id], [System.Title], [System.State] `
  FROM WorkItems `
  WHERE [System.AssignedTo] = @Me `
  AND [System.State] = 'Ready to Code' `
  ORDER BY [Microsoft.VSTS.Common.Priority]" --output table

# Activate the item
az boards work-item update --id ID --state Active
```

## 2. Create a Branch

```powershell
git checkout -b feature/ID-short-description
```

## 3. Create a PR Linked to Work Item

```powershell
az repos pr create `
  --title "feat: description" `
  --description "Resolves AB#ID" `
  --work-items ID `
  --auto-complete true `
  --delete-source-branch true
```

The `--work-items` flag links the PR to the work item. Use `AB#ID` in description for additional linking.

## 4. Monitor Pipeline on PR

```powershell
# List runs for the PR's branch
az pipelines runs list --branch feature/ID-short-description --top 1 --output table

# Check run details
az pipelines runs show --id RUN_ID --output table
```

## 5. Complete PR

```powershell
az repos pr update --id PR_ID --status completed
```

Work item state transitions automatically if board rules are configured.

## Assign to Self

Resolve the current user dynamically:

```powershell
$me = az account show --query "user.name" -o tsv
az boards work-item update --id ID --assigned-to $me
```
