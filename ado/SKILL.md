---
name: ado
description: Azure DevOps CLI for work items, PRs, pipelines, and backlog management. Triggers on: ADO, azure devops, work item, backlog, az boards, az repos, az pipelines.
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

## Reference Routing

Load the appropriate reference file based on what the user needs:

| User Intent | Reference File |
|-------------|---------------|
| Pick up work items, create branches, make PRs, monitor builds | `references/dev-flow.md` |
| Create features/stories, hierarchy, area paths, estimation | `references/planning-flow.md` |
| WIP, aging, throughput, cycle time, Kanban health | `references/backlog-management.md` |
| Pipeline status, failed builds, logs, triggers | `references/pipeline-debugging.md` |
| WIQL field names, operators, macros, quoting | `references/wiql-syntax.md` |
| CLI command patterns, bulk ops, REST API, output formatting | `references/command-cookbook.md` |
| Board columns, WIP limits, Kanban column queries | `resources/board-columns-api.md` |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `az account show` fails | Re-run `az login` — token expired |
| Empty query results | Check area path spelling; verify `FROM WorkItemLinks` gotcha (use REST API instead) |
| `charmap` encoding error | Use `az devops invoke` not `az rest`; set `$env:PYTHONIOENCODING = "utf-8"` |
| Defaults not set | Run `az devops configure --defaults organization=$config.organization project=$config.project` |
| Permission denied on work items | Verify area path permissions in ADO project settings |
| WIQL syntax error | Check quoting — double quotes outside, single quotes inside; see `references/wiql-syntax.md` |

## Tips

- Always use `--output table` for readable terminal output, `--output json` for parsing
- Use `--query` with JMESPath to filter JSON: `--query "[].{Id:id, Title:fields.\"System.Title\"}"`
- WIQL supports `@Me`, `@Today`, `@Today - N` macros
- Link PRs to work items with `AB#ID` in commit messages or PR descriptions
- Use `az devops wiki` commands for wiki operations
- Use `az boards iteration` and `az boards area` to manage team structure
