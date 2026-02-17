# AI Notes — Log

## 2026-02-13
- conventions: no Co-Authored-By or trailer attributions on commits — enforced in commit/SKILL.md rules
- conventions: closer/SKILL.md had a Co-Authored-By trailer contradicting the commit skill's no-attribution rule
- skills: SKILL.md files use YAML frontmatter (name, description) — description doubles as the trigger phrase list
- skills: phase-based structure with explicit mandatory/skip language is more effective than flat numbered lists for agent compliance
- skills: prime and prime-feat should both read .ainotes/summary.md — keeps agent context consistent whether loading project-level or feature-level context
- skills: daily-report is a custom skill (no scripts/) that orchestrates WorkIQ MCP + local file reads — pattern for skills that compose external tools with local filesystem

## 2026-02-17
- playwright-cli: skill uses extension-only mode (--extension --browser=msedge) to connect to user's running Edge browser via MCP Bridge extension — never launches a standalone browser
- playwright-cli: PLAYWRIGHT_MCP_EXTENSION_TOKEN loaded from ~/.copilot/skills/.env at session start; .env is gitignored
- playwright-cli: upstream repo is microsoft/playwright-cli (CLI) vs microsoft/playwright-mcp (MCP server) — CLI is preferred for coding agents due to token efficiency
- skills: allowed-tools frontmatter supports glob patterns like Bash(playwright-cli:*) to whitelist all subcommands of a CLI tool
