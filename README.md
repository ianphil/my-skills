# Ian's Skills Marketplace

A collection of reusable Claude Code plugin skills for enhanced AI-driven development workflows.

## Available Skills

### conversation-logging

Automatically log all Claude Code interactions to markdown files using global hooks. Track prompts, tool usage, and responses across all sessions.

**Features:**
- Logs every prompt, tool execution, and response with detailed context
- Organized by session in `~/.claude/conversation-logs/`
- Enables conversation replay and context sharing
- Includes prune script for cleaning old logs
- Useful for debugging and auditing

**Example usage:**
```bash
# View most recent conversation
cat $(ls -t ~/.claude/conversation-logs/*.md | head -1)

# Share context with Claude
claude -p "@~/.claude/conversation-logs/2026-01-04-session-a1b2c3d4.md What were we working on?"

# Search across all logs
grep -r "bug fix" ~/.claude/conversation-logs/

# Prune logs older than 14 days
~/.claude/hooks/prune-logs.sh
```

### astral-uv

Fast Python package and project management using [Astral's uv](https://github.com/astral-sh/uv).

**Features:**
- Virtual environment creation (10-100x faster than pip)
- Drop-in pip replacement with `uv pip install`
- Project initialization with `uv init`
- Python version management

**Example usage:**
```bash
uv venv              # Create virtual environment
uv add requests      # Add dependency to pyproject.toml
uv run script.py     # Run without manual venv activation
uv pip install -r requirements.txt  # Fast pip alternative
```

### spec-tests

Intent-based specification tests evaluated by LLM-as-judge. Tests capture WHY something matters, making them cheat-proof for LLM-driven development.

**Example test file** (`specs/tests/authentication.md`):
````markdown
---
target: src/auth.py
---
# Authentication Tests

### Valid Credentials Return Token

Users need immediate access after login. Failed authentication should not
expose whether email or password was wrong (security requirement).

```
Given valid credentials
When authenticate() is called
Then a JWT token is returned within 100ms
```
````

**Running tests:**
```bash
python specs/tests/run_tests_claude.py specs/tests/authentication.md
```

## Repository Structure

```
my-skills/
├── astral-uv/
│   └── SKILL.md
├── conversation-logging/
│   ├── SKILL.md
│   └── scripts/
├── glab/
│   └── SKILL.md
├── spec-tests/
│   ├── SKILL.md
│   └── scripts/
└── tmux-tdd/
    └── SKILL.md
```

## License

MIT
