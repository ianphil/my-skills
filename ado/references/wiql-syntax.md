# WIQL Query Reference

WIQL (Work Item Query Language) is used with `az boards query --wiql "..."`.

## Clause Structure

```sql
SELECT [Field1], [Field2]
FROM WorkItems                    -- or WorkItemLinks for link queries
WHERE [Condition1] AND [Condition2]
ORDER BY [Field] ASC|DESC
ASOF 'YYYY-MM-DD'                -- optional: historical point-in-time query
```

- `SELECT *` is **not supported** — you must list each field explicitly
- `FROM WorkItems` for flat queries, `FROM WorkItemLinks` for link/hierarchy queries
- `ASOF` must be the last clause; not compatible with link queries

## Field Names

Always use bracket syntax: `[System.FieldName]`.

### Common Fields

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
| `[System.BoardColumnDone]` | Whether in "done" split of column |

### Priority and Effort

| Field | Description |
|-------|-------------|
| `[Microsoft.VSTS.Common.Priority]` | Priority (1=Critical, 2=High, 3=Medium, 4=Low) |
| `[Microsoft.VSTS.Common.Severity]` | Bug severity |
| `[Microsoft.VSTS.Scheduling.StoryPoints]` | Story points |
| `[Microsoft.VSTS.Scheduling.Effort]` | Effort |
| `[Microsoft.VSTS.Common.ValueArea]` | Business or Architectural |

### Dates and History

| Field | Description |
|-------|-------------|
| `[Microsoft.VSTS.Common.ClosedDate]` | Date item was closed |
| `[Microsoft.VSTS.Common.ResolvedDate]` | Date item was resolved |
| `[Microsoft.VSTS.Common.ActivatedDate]` | Date item was activated |
| `[Microsoft.VSTS.Common.StateChangeDate]` | Last state change date |

## Operators

### Comparison

| Operator | Field Types | Example |
|----------|-------------|---------|
| `=` | All | `[System.State] = 'Active'` |
| `<>` | All | `[System.State] <> 'Removed'` |
| `>`, `<`, `>=`, `<=` | Number, Date | `[Microsoft.VSTS.Common.Priority] <= 2` |
| `IN` | String, Number | `[System.State] IN ('New', 'Active')` |
| `NOT IN` | String, Number | `[System.State] NOT IN ('Closed', 'Removed')` |

### Text Search

| Operator | Field Types | Indexed | Example |
|----------|-------------|---------|---------|
| `CONTAINS` | String (single-line) | **No** — slow substring scan | `[System.Title] CONTAINS 'auth'` |
| `NOT CONTAINS` | String (single-line) | No | `[System.Title] NOT CONTAINS 'test'` |
| `CONTAINS WORDS` | String, PlainText, HTML | **Yes** — fast full-text search | `[System.Description] CONTAINS WORDS 'authentication failed'` |
| `NOT CONTAINS WORDS` | String, PlainText, HTML | Yes | `[System.Description] NOT CONTAINS WORDS 'obsolete'` |

**CONTAINS vs CONTAINS WORDS — critical difference:**
- `CONTAINS 'auth'` → substring match: finds "auth", "Authorize", "Authentication"
- `CONTAINS WORDS 'auth'` → word-boundary match with stemming: finds "auth" as a whole word, supports stemming ("run" matches "running")
- Use `CONTAINS WORDS` for Description/repro steps (faster, indexed). Use `CONTAINS` for Title/Tags (short fields, substring needed).
- `CONTAINS WORDS` limit: 100 characters max in search phrase

### Path Operators

| Operator | Field Types | Example |
|----------|-------------|---------|
| `UNDER` | AreaPath, IterationPath | `[System.AreaPath] UNDER 'Secure Cloud Access\Azure Encrypted Transport'` |
| `NOT UNDER` | AreaPath, IterationPath | `[System.IterationPath] NOT UNDER 'Project\Old'` |

`UNDER` matches the path itself **and all children** beneath it.

### Identity Operators

| Operator | Field Types | Example |
|----------|-------------|---------|
| `IN GROUP` | Identity fields | `[System.AssignedTo] IN GROUP 'My Team'` |
| `NOT IN GROUP` | Identity fields | `[System.AssignedTo] NOT IN GROUP 'Contractors'` |

`IN GROUP` checks membership in an ADO security group or team — useful for "all items assigned to anyone on my team".

### Historical Operators

| Operator | Field Types | Example |
|----------|-------------|---------|
| `WAS EVER` | Identity, State, picklist | `[System.AssignedTo] WAS EVER 'alice@example.com'` |
| `EVER` | State | `[System.State] EVER 'Active'` |

`WAS EVER` checks if a field **ever had** a particular value at any point in history. Works on identity and picklist fields, not just State.

### Null Checks

| Operator | Example |
|----------|---------|
| `= ''` | `[System.AssignedTo] = ''` (unassigned) |
| `<> ''` | `[System.AssignedTo] <> ''` (assigned) |

## Macros

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

**Warning:** `@CurrentIteration` requires team context and may not resolve in all CLI contexts. Use explicit iteration paths when querying via `az boards query`.

## Query Patterns

### Basic SELECT

```sql
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.WorkItemType] = 'User Story'
  AND [System.State] = 'Active'
ORDER BY [Microsoft.VSTS.Common.Priority]
```

### Historical Query (ASOF)

See the state of work items as of a past date:

```sql
SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] = 'User Story'
  AND [System.State] = 'Active'
ORDER BY [System.ChangedDate] DESC
ASOF '2025-01-15'
```

- Date format: `'YYYY-MM-DD'` (ISO 8601 recommended)
- Cannot be used with `FROM WorkItemLinks` (flat queries only)
- Returns work item data as it existed on that date

### Hierarchical (Parent-Child)

**⚠️ CRITICAL:** `az boards query` silently returns empty results for `FROM WorkItemLinks` queries. Link queries only work via the REST API. Use `az devops invoke` instead:

```powershell
# Save WIQL to a temp file (required for POST body)
$body = '{"query": "SELECT [System.Id], [System.Title] FROM WorkItemLinks WHERE (Source.[System.Id] = 12345) AND ([System.Links.LinkType] = ''System.LinkTypes.Hierarchy-Forward'') MODE (MustContain)"}'
$body | Out-File -Encoding utf8 wiql-query.json

az devops invoke `
  --area wit `
  --resource wiql `
  --http-method POST `
  --api-version 7.0 `
  --route-parameters project="Secure Cloud Access" `
  --in-file wiql-query.json `
  --output json

Remove-Item wiql-query.json
```

The response contains `workItemRelations` with source/target ID pairs — you must fetch full work item details separately.

For **flat queries** that find children without link syntax, use the simpler approach:

```sql
-- Find features under an epic (if you know the parent ID, use relation show instead)
SELECT [System.Id], [System.Title], [System.WorkItemType]
FROM WorkItems
WHERE [System.WorkItemType] = 'Feature'
  AND [System.AreaPath] UNDER 'Secure Cloud Access\Azure Encrypted Transport'
```

Or use `az boards work-item relation show --id PARENT_ID` to list children directly.

### Link Query WIQL Syntax (for REST API)

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

### Related Links

```sql
SELECT [System.Id], [System.Title]
FROM WorkItemLinks
WHERE (Source.[System.Id] = 12345)
  AND ([System.Links.LinkType] = 'System.LinkTypes.Related-Forward')
MODE (MustContain)
```

### Link Query Modes

| Mode | Behavior |
|------|----------|
| `MustContain` | Only return items that have matching links |
| `MayContain` | Return items regardless of whether they have matching links |
| `DoesNotContain` | Only return items that do NOT have matching links |
| `Recursive` | Traverse hierarchy recursively (all descendants) |

Modes can be combined: `MODE (Recursive, MustContain)`

### Common Link Types

| Link Type | Description |
|-----------|-------------|
| `System.LinkTypes.Hierarchy-Forward` | Parent → Child |
| `System.LinkTypes.Hierarchy-Reverse` | Child → Parent |
| `System.LinkTypes.Related-Forward` | Related item |
| `System.LinkTypes.Dependency-Forward` | Successor (depends on) |
| `System.LinkTypes.Dependency-Reverse` | Predecessor |

List all link types in your org: `az boards work-item relation list-type --output table`

## az boards query Usage

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

## PowerShell Quoting for WIQL

Getting quotes right in PowerShell is the #1 source of WIQL errors via CLI.

### Rules

1. **Outer quotes**: Use double quotes `"` to wrap the `--wiql` value
2. **Inner string values**: Use single quotes `'` inside WIQL (standard WIQL syntax)
3. **Escaping single quotes in values**: Double them up: `''` → literal `'`

### Examples

```powershell
# Standard query — double outside, single inside
az boards query --wiql "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'" --output table

# Value containing a single quote (O'Brien) — double up the inner quote
az boards query --wiql "SELECT [System.Id] FROM WorkItems WHERE [System.Title] CONTAINS 'O''Brien'"

# Multi-line query in PowerShell (use backtick for continuation)
az boards query --wiql "SELECT [System.Id], [System.Title], [System.State] `
  FROM WorkItems `
  WHERE [System.WorkItemType] = 'User Story' `
  AND [System.State] = 'Active' `
  AND [System.AreaPath] UNDER 'Secure Cloud Access\Azure Encrypted Transport' `
  ORDER BY [Microsoft.VSTS.Common.Priority]" --output table

# Store WIQL in a variable for complex queries
$wiql = @"
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.WorkItemType] = 'User Story'
  AND [System.State] IN ('New', 'Active')
  AND [System.AreaPath] UNDER 'Secure Cloud Access\Azure Encrypted Transport\SWE'
ORDER BY [System.ChangedDate] DESC
"@
az boards query --wiql $wiql --output table
```

**Tip:** For complex queries, the here-string (`@"..."@`) approach avoids all quoting headaches.

## Gotchas

### Quoting and Syntax
- String values use **single quotes** inside WIQL: `'Active'` not `"Active"`
- WIQL strings can also use double quotes, but single is conventional and avoids shell conflicts
- To embed a literal single quote in a value, double it: `'O''Brien'`
- Field names are **case-insensitive** but bracket syntax `[...]` is required
- `SELECT *` is **not supported** — always list fields explicitly

### Operators
- `CONTAINS` is a **slow unindexed substring scan** — avoid on large result sets
- `CONTAINS WORDS` is **fast indexed full-text** — prefer for Description, repro steps
- `CONTAINS WORDS` supports **stemming** ("run" matches "running") — may over-match
- `UNDER` matches the path itself AND all children beneath it
- `WAS EVER` works on identity and picklist fields, not just `[System.State]`

### Dates
- Date comparisons use **server timezone**, not local timezone
- **No date arithmetic between fields** — `[ClosedDate] - [CreatedDate]` is NOT supported
- Compute date differences outside WIQL (PowerShell, Python, etc.)
- `@Today` resolves to midnight server time

### Limits and Restrictions
- Maximum **20,000 results** per query
- `ORDER BY` only supports one field, ascending (default) or `DESC`
- `ASOF` is **not compatible** with `FROM WorkItemLinks` (flat queries only)
- **`az boards query` silently returns empty for `FROM WorkItemLinks`** — use `az devops invoke` with REST API for link/hierarchy queries
- `@CurrentIteration` requires team context — may fail in CLI without team scope
- REST API WIQL endpoint returns **only IDs** — a second call is needed to fetch field values
- Area/iteration paths should **not contain quotes** — there is no escape mechanism for them
- `--fields` and `--expand` **cannot be used together** on `az boards work-item show`
