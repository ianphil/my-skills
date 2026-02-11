# Backlog Management — Kanban Metrics & Queries

> Load this file when the user asks about WIP, aging items, throughput, cycle time, state distribution, or Kanban board health. For board column configuration and WIP limits, also read `resources/board-columns-api.md`.

All metrics use WIQL queries via `az boards query`. For WIQL language reference (fields, operators, macros), see `references/wiql-syntax.md`.

## WIP — Items in Progress

```powershell
az boards query --wiql "SELECT [System.Id], [System.Title], [System.AssignedTo] `
  FROM WorkItems `
  WHERE [System.State] = 'Active' `
  AND [System.WorkItemType] = 'User Story' `
  ORDER BY [System.ChangedDate]" --output table
```

## Aging — Items Stale in a State

Find items stuck in Active for more than 7 days:

```powershell
az boards query --wiql "SELECT [System.Id], [System.Title], [System.ChangedDate] `
  FROM WorkItems `
  WHERE [System.State] = 'Active' `
  AND [System.ChangedDate] < @Today - 7 `
  AND [System.WorkItemType] = 'User Story'" --output table
```

## Throughput — Recently Completed

Items closed in the last 14 days:

```powershell
az boards query --wiql "SELECT [System.Id], [System.Title], [System.ChangedDate] `
  FROM WorkItems `
  WHERE [System.State] = 'Closed' `
  AND [System.ChangedDate] >= @Today - 14 `
  AND [System.WorkItemType] = 'User Story' `
  ORDER BY [System.ChangedDate] DESC" --output table
```

## State Distribution

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

## Cycle Time

Query items with state change history (requires REST API for full history):

```powershell
az devops invoke `
  --area wit `
  --resource revisions `
  --route-parameters project=$config.project workItemId=ID `
  --api-version 7.0
```
