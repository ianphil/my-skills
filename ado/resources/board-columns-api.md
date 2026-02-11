# Fetching Board Columns via ADO REST API

> Load this file when the user asks about board columns, WIP limits, or Kanban column configuration. For board-level metric queries, see `references/backlog-management.md`.

The `az boards` CLI doesn't expose board column configuration directly. Use `az devops invoke` to hit the Boards REST API.

## Step 1: List Boards for a Team

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

## Step 2: Fetch Columns for a Specific Board

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

## Gotchas

- **Do NOT use `az rest`** for this endpoint — the response contains Unicode characters (e.g., `∞` U+221E) that cause `charmap` encoding errors on Windows (`'charmap' codec can't encode character '\u221e'`).
- **Use `az devops invoke`** instead, which handles encoding correctly.
- The list endpoint (`--resource boards` without `id`) returns board metadata only (no columns). You must pass the board `id` as a route parameter to get column details.
- Set `$env:PYTHONIOENCODING = "utf-8"` as a safety net for encoding issues.

## Step 3: Query Work Items by Board Column

Board columns like "PR", "Testing", "Deployment" may share the same underlying state (e.g., "Active"). Use the `System.BoardColumn` field in WIQL to query items in a specific column:

```powershell
az boards query --wiql "SELECT [System.Id], [System.Title], [System.AssignedTo], [System.BoardColumn] `
  FROM WorkItems `
  WHERE [System.WorkItemType] = 'User Story' `
  AND [System.AreaPath] UNDER $config.areaPaths.story `
  AND [System.BoardColumn] = 'PR' `
  AND [System.State] <> 'Removed' `
  ORDER BY [System.ChangedDate] DESC" --output table
```

### Available Board Column Values

These match the column names from Step 2. For the Stories board:

| Board Column | Underlying State | WIP Limit |
|-------------|-----------------|-----------|
| New | New | none |
| Ready | Ready to Code | none |
| Active | Active | 8 |
| PR | Active | 5 |
| Testing | Active | 3 |
| Deployment | Active | 3 |
| Closed | Closed | none |

### Key Insight

Multiple board columns can map to the same ADO state (e.g., "PR", "Testing", "Deployment" all map to "Active"). Querying by `System.State = 'Active'` returns items across all those columns. Use `System.BoardColumn` for precise column-level queries.

### Check WIP Compliance

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

## API Reference

- [Boards - Get](https://learn.microsoft.com/en-us/rest/api/azure/devops/work/boards/get) — `GET {org}/{project}/{team}/_apis/work/boards/{board}?api-version=7.0`
- [Boards - List](https://learn.microsoft.com/en-us/rest/api/azure/devops/work/boards/list) — `GET {org}/{project}/{team}/_apis/work/boards?api-version=7.0`
- [WIQL BoardColumn](https://learn.microsoft.com/en-us/azure/devops/boards/queries/query-by-workflow-changes) — `System.BoardColumn` field reference
