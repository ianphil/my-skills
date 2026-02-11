---
name: ado
description: "Azure DevOps CLI (az ado). Use for work items, PRs, pipelines, and backlog management. Triggers on: az ado, ADO, azure devops, work item, backlog, az boards, az repos, az pipelines."
---

# ado — Azure DevOps CLI

Interact with Azure DevOps using the `az devops` CLI extension. Assumes `az login` authentication and org/project defaults are configured.

## Configuration

On first use, check for `ado/config.json` in the skill directory. If it doesn't exist, ask the user these questions and save the answers:

1. What is your ADO organization URL? (e.g., `https://dev.azure.com/myorg`)
2. What is your project name?
3. What area path should Epics use?
4. What area path should Features/Stories/Tasks/Bugs use?
5. What iteration path should work items use?

Save to `ado/config.json` (gitignored — never committed). Config shape:

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

Read config at the start of any operation:

```powershell
$config = Get-Content "$PSScriptRoot\..\ado\config.json" | ConvertFrom-Json
```

## Prerequisites

Verify auth and defaults before any operation:

```powershell
az account show --query "{name:name, user:user.name}" -o table
az devops configure --list
```

If defaults are missing:

```powershell
az devops configure --defaults organization=$config.organization project=$config.project
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
az boards work-item update --id ID --state "Ready to Review"
az boards work-item update --id ID --state "Ready to Code"
az boards work-item update --id ID --state Active
az boards work-item update --id ID --state Closed
```

## Quick Reference

Essential commands. **For detailed patterns, load the appropriate reference file from the routing table below.**

```powershell
# Show a work item
az boards work-item show --id ID --output table

# Show with relations (children, parent, related)
az boards work-item show --id ID --expand relations --output json

# Get child IDs from a parent (e.g., features under an epic)
$json = az boards work-item show --id PARENT_ID --expand relations --output json | ConvertFrom-Json
$childIds = $json.relations | Where-Object { $_.attributes.name -eq 'Child' } | ForEach-Object { $_.url -replace '.*/', '' }

# Show multiple work items (loop — there is no --ids flag)
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

## Reference Routing

**Before executing any multi-step operation, you MUST read the matching reference file.** Do not rely solely on the quick reference above for anything beyond simple single commands.

| User Intent | Reference File | **Read BEFORE** |
|-------------|---------------|-----------------|
| Pick up work items, create branches, make PRs, monitor builds | `references/dev-flow.md` | Any PR or branch workflow |
| Create features/stories, hierarchy, area paths, estimation | `references/planning-flow.md` | Creating or linking work items |
| WIP, aging, throughput, cycle time, Kanban health | `references/backlog-management.md` | Any backlog query or metric |
| Pipeline status, failed builds, logs, triggers | `references/pipeline-debugging.md` | Any pipeline operation |
| WIQL field names, operators, macros, quoting | `references/wiql-syntax.md` | Writing any WIQL query |
| CLI command patterns, bulk ops, REST API, output formatting | `references/command-cookbook.md` | Bulk operations or REST API calls |
| Board columns, WIP limits, Kanban column queries | `resources/board-columns-api.md` | Any board column query |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `az account show` fails | Re-run `az login` — token expired |
| Empty query results | Check area path spelling; verify `FROM WorkItemLinks` gotcha (use REST API instead) |
| `charmap` encoding error | Use `az devops invoke` not `az rest`; set `$env:PYTHONIOENCODING = "utf-8"` |
| Defaults not set | Run `az devops configure --defaults organization=$config.organization project=$config.project` |
| Permission denied on work items | Verify area path permissions in ADO project settings |
| WIQL syntax error | Check quoting — double quotes outside, single quotes inside; see `references/wiql-syntax.md` |

## Rules

- **Always use PowerShell for all scripting and JSON processing** — never pipe to `python`, `node`, or other languages. Use `ConvertFrom-Json`, `Select-Object`, `Where-Object`, `ForEach-Object`, and other PowerShell cmdlets for all data manipulation.
- Use `--query` with JMESPath on `az` commands to filter JSON before it reaches PowerShell when possible.
- **If a command is NOT in the quick reference above, STOP and read the appropriate reference file from the routing table before proceeding.** Never guess at `az` CLI flags or parameters — look them up first.

## Tips

- Always use `--output table` for readable terminal output, `--output json` for parsing
- Use `--query` with JMESPath to filter JSON: `--query "[].{Id:id, Title:fields.\"System.Title\"}"`
- WIQL supports `@Me`, `@Today`, `@Today - N` macros
- Link PRs to work items with `AB#ID` in commit messages or PR descriptions
- Use `az devops wiki` commands for wiki operations
- Use `az boards iteration` and `az boards area` to manage team structure
