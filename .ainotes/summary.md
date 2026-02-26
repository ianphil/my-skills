# AI Notes — Skills Marketplace

## Project Overview
Collection of AI coding agent skills for GitHub Copilot CLI. Each skill lives in `<name>/SKILL.md` at the repo root with optional `scripts/` and `references/` directories.

## Skill Creation
- Use the `skill-development` custom skill (or `/skill-creator`) to create new skills per `AGENTS.md`
- SKILL.md files use YAML frontmatter with `name` and `description` fields

## Skills Inventory
| Skill | Description |
|-------|-------------|
| ado | Azure DevOps CLI for work items, PRs, pipelines |
| ainotes | Consolidate/summarize accumulated agent notes |
| astral-uv | Fast Python package management with uv |
| autopilot | Auto-implement all phases of a feature sequentially |
| closer | Archive/complete a feature, move to _completed/ |
| commit | Stage all changes and push to remote |
| conversation-logging | Log conversation events to markdown files |
| glab | GitLab CLI for MRs, issues, CI/CD |
| implement | Execute tasks with TDD red-green-refactor workflow |
| implement-agents | Parallel multi-agent implementation |
| planner | Comprehensive feature planning with TDD task breakdown |
| playwright-cli | Browse web via Edge browser MCP Bridge |
| prime | Load project context (README, ainotes, git ls-files) |
| prime-feat | Load context for a specific feature number |
| quick-plan | Lightweight plan creation in backlog/plans/ |
| share-transcript | Publish session as GitHub Gist |
| spec-tests | Intent-based specification tests (LLM-as-judge) |
| tmux-tdd | TDD workflows via tmux panes |
| work-plan | Show phase breakdown and progress for a feature |
| workiq | Work item intelligence/querying |

## Key Files
- `AGENTS.md` — repo conventions, skill structure rules
- `README.md` — project overview
- `scripts/Sync-Skills.ps1` — sync skills script
- `spec-tests/` — most developed skill, has scripts + specs directories
