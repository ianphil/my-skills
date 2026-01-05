---
name: conversation-logging
description: Global hooks for logging Claude Code conversation events to markdown files. Tracks prompts, tool usage, and responses across all sessions. Useful for debugging, auditing, and providing conversation context to Claude.
---

# Conversation Logging Skill

Automatically log all Claude Code interactions to structured markdown files using global hooks. Enables conversation replay, debugging, and context sharing between sessions.

## What Gets Logged

- **User prompts**: Every prompt submitted to Claude
- **Tool executions**: Which tools were used and when
- **Session metadata**: Working directory, timestamps, session IDs
- **Response completion**: When Claude finishes each response

## Installation

### Step 1: Create Hook Script

Create the logging hook at `~/.claude/hooks/log-conversation.sh`:

```bash
#!/bin/bash
# Global hook to log Claude Code conversation events

LOG_DIR="$HOME/.claude/conversation-logs"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE_FILE="$LOG_DIR/$(date '+%Y-%m-%d').md"

mkdir -p "$LOG_DIR"

# Read JSON input from stdin
INPUT=$(cat)

# Extract key fields using jq if available, otherwise use simple grep
if command -v jq &> /dev/null; then
    EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // "unknown"')
    CWD=$(echo "$INPUT" | jq -r '.cwd // "unknown"')
    TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
    PROMPT=$(echo "$INPUT" | jq -r '.prompt // ""')
else
    EVENT="unknown"
    CWD=$(pwd)
fi

# Log based on event type
case "$EVENT" in
    UserPromptSubmit)
        cat >> "$DATE_FILE" <<EOF

---
## [$TIMESTAMP] User Prompt Submitted
**Working Directory:** \`$CWD\`

\`\`\`
$PROMPT
\`\`\`

EOF
        ;;

    PostToolUse)
        if [ -n "$TOOL" ]; then
            echo "### [$TIMESTAMP] Tool: $TOOL" >> "$DATE_FILE"
            echo "" >> "$DATE_FILE"
        fi
        ;;

    Stop)
        echo "### [$TIMESTAMP] Claude Response Complete" >> "$DATE_FILE"
        echo "" >> "$DATE_FILE"
        ;;
esac

exit 0
```

Make it executable:
```bash
chmod +x ~/.claude/hooks/log-conversation.sh
```

### Step 2: Configure Global Hooks

Add hooks to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/log-conversation.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/log-conversation.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/log-conversation.sh"
          }
        ]
      }
    ]
  }
}
```

If you already have other settings in your `settings.json`, merge the `hooks` section carefully.

### Step 3: Verify Installation

Run any Claude Code command and check the logs:

```bash
# Check today's log
cat ~/.claude/conversation-logs/$(date +%Y-%m-%d).md

# List all conversation logs
ls -lh ~/.claude/conversation-logs/
```

## Usage

### Viewing Conversation Logs

**Today's conversations:**
```bash
cat ~/.claude/conversation-logs/$(date +%Y-%m-%d).md
```

**Specific date:**
```bash
cat ~/.claude/conversation-logs/2026-01-05.md
```

**Recent logs:**
```bash
ls -lt ~/.claude/conversation-logs/ | head -5
```

**Search across all logs:**
```bash
grep -r "search term" ~/.claude/conversation-logs/
```

### Providing Context to Claude

When you want Claude to understand a previous conversation:

**Option 1: Direct file reference**
```
Read my conversation log from yesterday:
@~/.claude/conversation-logs/2026-01-04.md

What were we working on?
```

**Option 2: Copy relevant sections**
```
Here's what happened in my last session:

[paste relevant log sections]

Continue from where we left off.
```

**Option 3: Search and reference**
```bash
# Find the conversation about a topic
grep -l "GitHub Issues" ~/.claude/conversation-logs/*.md
```

Then reference that file with `@` in Claude Code.

### Debugging Failed Sessions

When Claude encounters errors or you need to replay a session:

```bash
# Find failed tool executions
grep -A 5 "Tool: Bash" ~/.claude/conversation-logs/$(date +%Y-%m-%d).md

# See what prompts led to errors
grep -B 10 "error" ~/.claude/conversation-logs/$(date +%Y-%m-%d).md
```

### Resuming Work Across Sessions

Use conversation logs to pick up where you left off:

```bash
# View yesterday's work
cat ~/.claude/conversation-logs/$(date -d yesterday +%Y-%m-%d).md

# Share with Claude
claude -p "Read @~/.claude/conversation-logs/$(date -d yesterday +%Y-%m-%d).md and summarize what we were working on"
```

## Log Format

Each log file is organized chronologically:

```markdown
---
## [2026-01-05 14:23:15] User Prompt Submitted
**Working Directory:** `/home/user/project`

```
Implement the login feature
```

### [2026-01-05 14:23:16] Tool: Read
### [2026-01-05 14:23:17] Tool: Edit
### [2026-01-05 14:23:18] Tool: Write
### [2026-01-05 14:23:20] Claude Response Complete

---
## [2026-01-05 14:25:30] User Prompt Submitted
...
```

## Customization

### Change Log Location

Edit the script's `LOG_DIR` variable:

```bash
LOG_DIR="$HOME/my-custom-logs"
```

### Add More Details

Extend the script to log additional fields from the hook input:

```bash
# Log model info
MODEL=$(echo "$INPUT" | jq -r '.model // "unknown"')

# Log session ID
SESSION=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
```

### Filter Specific Tools

Only log certain tools:

```bash
PostToolUse)
    # Only log Read, Write, Edit tools
    if [[ "$TOOL" =~ ^(Read|Write|Edit)$ ]]; then
        echo "### [$TIMESTAMP] Tool: $TOOL" >> "$DATE_FILE"
    fi
    ;;
```

### JSON Logs Instead of Markdown

Replace the logging logic to output JSON:

```bash
echo "$INPUT" | jq '.' >> "$LOG_DIR/$(date +%Y-%m-%d).jsonl"
```

## Troubleshooting

**Logs not being created?**
- Check hook script is executable: `ls -l ~/.claude/hooks/log-conversation.sh`
- Verify settings.json syntax: `cat ~/.claude/settings.json | jq .`
- Check for hook errors: Hook failures are silent by default

**Logs are empty or incomplete?**
- Install `jq` for better parsing: `sudo apt install jq` (Linux) or `brew install jq` (macOS)
- Check script permissions on log directory: `ls -ld ~/.claude/conversation-logs`

**Want to disable logging temporarily?**
- Comment out hooks in `~/.claude/settings.json`
- Or rename the hook script: `mv ~/.claude/hooks/log-conversation.sh{,.disabled}`

## Privacy & Security

**Important considerations:**

- Logs contain **all prompts** you send to Claude, including potentially sensitive info
- Logs are stored **unencrypted** in your home directory
- Logs persist **indefinitely** unless manually cleaned up

**Recommendations:**

1. **Regular cleanup**: Delete old logs you don't need
   ```bash
   # Delete logs older than 30 days
   find ~/.claude/conversation-logs -name "*.md" -mtime +30 -delete
   ```

2. **Exclude from backups**: Add to `.gitignore` or backup exclusions
   ```bash
   echo "conversation-logs/" >> ~/.gitignore_global
   ```

3. **Encrypt sensitive logs**:
   ```bash
   gpg -c ~/.claude/conversation-logs/2026-01-05.md
   rm ~/.claude/conversation-logs/2026-01-05.md
   ```

## Advanced: Per-Project Logs

To log per-project instead of globally, use project-specific hooks in `.claude/settings.json` within each project:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'cat >> .claude/conversation.md'"
          }
        ]
      }
    ]
  }
}
```

Add `.claude/conversation.md` to your `.gitignore`.

## Quick Reference

| Task | Command |
|------|---------|
| View today's log | `cat ~/.claude/conversation-logs/$(date +%Y-%m-%d).md` |
| List all logs | `ls -lh ~/.claude/conversation-logs/` |
| Search logs | `grep -r "search term" ~/.claude/conversation-logs/` |
| Clean old logs | `find ~/.claude/conversation-logs -mtime +30 -delete` |
| Share with Claude | `@~/.claude/conversation-logs/YYYY-MM-DD.md` |
| Disable logging | Rename hook script to `.disabled` |

## See Also

- [Claude Code Hooks Documentation](https://docs.anthropic.com/claude-code/hooks) - Full hooks reference
- [MCP Logging](https://modelcontextprotocol.io) - Alternative logging via MCP servers
