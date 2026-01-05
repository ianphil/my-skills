#!/bin/bash
# Global hook to log Claude Code conversation events
# Handles multiple concurrent Claude instances by using unique session IDs

LOG_DIR="$HOME/.claude/conversation-logs"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE=$(date '+%Y-%m-%d')

mkdir -p "$LOG_DIR"

# Read JSON input from stdin
INPUT=$(cat)

# Extract key fields using jq if available
if command -v jq &> /dev/null; then
    EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // "unknown"')
    CWD=$(echo "$INPUT" | jq -r '.cwd // "unknown"')
    TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
    PROMPT=$(echo "$INPUT" | jq -r '.prompt // ""')
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // ""')
else
    EVENT="unknown"
    CWD=$(pwd)
    SESSION_ID=""
fi

# Create unique log file per session
# Format: YYYY-MM-DD-session-XXXXX.md
if [ -n "$SESSION_ID" ]; then
    # Extract first 8 chars of session ID for readability
    SHORT_SESSION="${SESSION_ID:0:8}"
    LOG_FILE="$LOG_DIR/${DATE}-session-${SHORT_SESSION}.md"
else
    # Fallback: use PID if session_id not available
    LOG_FILE="$LOG_DIR/${DATE}-pid-$$.md"
fi

# Initialize log file with header if it doesn't exist
if [ ! -f "$LOG_FILE" ]; then
    cat > "$LOG_FILE" <<EOF
# Claude Code Conversation Log
**Date:** $DATE
**Session ID:** ${SESSION_ID:-unknown}
**Started:** $TIMESTAMP

---

EOF
fi

# Log based on event type
case "$EVENT" in
    UserPromptSubmit)
        cat >> "$LOG_FILE" <<EOF

## [$TIMESTAMP] User Prompt
**Working Directory:** \`$CWD\`

\`\`\`
$PROMPT
\`\`\`

EOF
        ;;

    PostToolUse)
        if [ -n "$TOOL" ]; then
            echo "### [$TIMESTAMP] Tool: \`$TOOL\`" >> "$LOG_FILE"
            echo "" >> "$LOG_FILE"
        fi
        ;;

    Stop)
        echo "### [$TIMESTAMP] Response Complete" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
        ;;
esac

exit 0
