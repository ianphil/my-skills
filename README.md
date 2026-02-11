# Ian's Skills Marketplace

A collection of reusable Claude Code plugin skills for enhanced AI-driven development workflows.

## Available Skills

### ADO & DevOps

| Skill | Description |
|-------|-------------|
| **ado** | Azure DevOps CLI — work items, PRs, pipelines, repos, Kanban backlog management |
| **glab** | GitLab CLI — merge requests, issues, CI/CD pipelines |
| **commit** | Stage, commit, and push changes with conventional commit messages |

### Planning & Workflow

| Skill | Description |
|-------|-------------|
| **planner** | Comprehensive feature planning — analysis, spec, research, design, TDD tasks |
| **quick-plan** | Lightweight plan capture for later expansion |
| **work-plan** | View phase breakdown, progress status, and next actions |
| **implement** | Execute tasks following strict TDD red-green-refactor workflow |
| **implement-agents** | Orchestrate multiple agents running /implement in parallel |
| **autopilot** | Run all phases of a feature sequentially without manual intervention |
| **closer** | Move finished features to the _completed/ directory |

### Context & Navigation

| Skill | Description |
|-------|-------------|
| **prime** | Load project context and understand codebase structure |
| **prime-feat** | Load all planning artifacts for a specific feature |

### Testing

| Skill | Description |
|-------|-------------|
| **spec-tests** | Intent-based specification tests evaluated by LLM-as-judge |
| **tmux-tdd** | Interact with tmux-based TDD environments |

### Tooling

| Skill | Description |
|-------|-------------|
| **astral-uv** | Fast Python package and project management using Astral's uv |
| **conversation-logging** | Log all Claude Code interactions to markdown files |
| **share-transcript** | Publish Claude Code sessions as GitHub Gists |

## Repository Structure

```
my-skills/
├── ado/
│   ├── SKILL.md
│   └── references/
├── astral-uv/
│   └── SKILL.md
├── autopilot/
│   └── SKILL.md
├── closer/
│   └── SKILL.md
├── commit/
│   └── SKILL.md
├── conversation-logging/
│   ├── SKILL.md
│   └── scripts/
├── glab/
│   └── SKILL.md
├── implement/
│   └── SKILL.md
├── implement-agents/
│   └── SKILL.md
├── planner/
│   ├── SKILL.md
│   └── references/
├── prime/
│   └── SKILL.md
├── prime-feat/
│   └── SKILL.md
├── quick-plan/
│   └── SKILL.md
├── share-transcript/
│   └── SKILL.md
├── spec-tests/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
├── tmux-tdd/
│   └── SKILL.md
├── work-plan/
│   ├── SKILL.md
│   └── references/
└── scripts/
    └── Sync-Skills.ps1
```

## License

MIT
