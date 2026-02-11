# Planning Flow — Features, Stories, Hierarchy & Estimation

> Load this file when the user asks about creating features/stories, building work item hierarchies, setting area/iteration paths, writing acceptance criteria, or estimating story points.

## Path Conventions

Paths come from `ado/config.json`. The table below shows the config keys:

| Work Item Type | Area Path (config key) | Iteration Path (config key) |
|----------------|------------------------|----------------------------|
| Epic | `areaPaths.epic` | `iterationPath` |
| Feature | `areaPaths.feature` | `iterationPath` |
| User Story | `areaPaths.story` | `iterationPath` |
| Task | `areaPaths.task` | `iterationPath` |
| Bug | `areaPaths.bug` | `iterationPath` |

## Descriptions and Acceptance Criteria

| Work Item Type | Description Field | Acceptance Criteria |
|----------------|-------------------|---------------------|
| Feature | `--description` (put AC here) | N/A — use description |
| User Story | `--description` (user story text) | `--fields "Microsoft.VSTS.Common.AcceptanceCriteria=..."` |

Both fields accept HTML. Use `<ul><li>` for bullet lists:

```powershell
$config = Get-Content "$PSScriptRoot\..\config.json" | ConvertFrom-Json

# Feature — AC goes in description
az boards work-item update --id FEATURE_ID `
  --description "<h3>Acceptance Criteria</h3><ul><li>Criterion 1</li><li>Criterion 2</li></ul>"

# Story — description for the story, AC in its own field
az boards work-item update --id STORY_ID `
  --description "As a user, I want to..." `
  --fields "Microsoft.VSTS.Common.AcceptanceCriteria=<ul><li>Criterion 1</li><li>Criterion 2</li></ul>"
```

## Create a Feature Under an Epic

Create the feature, then link it to the parent epic:

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

## Create Stories Under a Feature

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

## Bulk Story Creation

Create multiple stories under a feature by chaining create + link:

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

## Set Iteration and Area Paths

```powershell
az boards work-item update --id ID `
  --area $config.areaPaths.story `
  --iteration $config.iterationPath
```

## Estimation (Story Points)

Story points use the scale from `config.json` (default: first 10 Fibonacci numbers).

When asked to "estimate stories", assess complexity and set story points:

```powershell
az boards work-item update --id ID `
  --fields "Microsoft.VSTS.Scheduling.StoryPoints=5"
```

Bulk estimate multiple stories:

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

### Complexity Guide

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
