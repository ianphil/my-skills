# Ian's Skills Marketplace

A collection of reusable Claude Code plugin skills for enhanced AI-driven development workflows.

## Installation

Add this plugin to your Claude Code configuration:

```bash
claude plugins add ian-skills
```

Or add manually to your `.claude/settings.json`:

```json
{
  "plugins": ["ian-skills@claude-code-plugins"]
}
```

## Available Skills

### conversation-logging

Automatically log all Claude Code interactions to markdown files using global hooks. Track prompts, tool usage, and responses across all sessions.

**Features:**
- Logs every prompt, tool execution, and response
- Organized by date in `~/.claude/conversation-logs/`
- Enables conversation replay and context sharing
- Useful for debugging and auditing

**Example usage:**
```bash
# View today's conversations
cat ~/.claude/conversation-logs/$(date +%Y-%m-%d).md

# Share context with Claude
claude -p "@~/.claude/conversation-logs/2026-01-04.md What were we working on?"

# Search across all logs
grep -r "bug fix" ~/.claude/conversation-logs/
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

### literate-tests

Create and run markdown-based test suites that agents can execute autonomously. Tests serve as both documentation and executable specifications.

**Supported languages:**
- Python
- JavaScript / TypeScript
- Bash / Shell
- PowerShell
- Rust
- C#

**Example test file** (`tests/parser.md`):
````markdown
---toml
module = "mypackage.parser"
import = ["parse", "ParseError"]
---

# Parser Tests

## Valid Input

```py
result = parse("hello world")
result.tokens  # expect: ["hello", "world"]
```

## Error Handling

```py
parse(None)  # error: [null-input]
```
````

**Running tests:**
```bash
python scripts/run_tests.py tests/parser.md
```

## Repository Structure

```
my-skills/
├── .claude-plugin/
│   └── marketplace.json    # Plugin manifest
└── skills/
    ├── astral-uv/
    │   └── SKILL.md
    └── literate-tests/
        ├── SKILL.md
        └── scripts/        # Language-specific test runners
            ├── run_tests.py
            ├── run_tests.js
            ├── run_tests.ts
            ├── run_tests.sh
            ├── run_tests.ps1
            ├── run_tests.rs
            └── RunTests.cs
```

## License

MIT
