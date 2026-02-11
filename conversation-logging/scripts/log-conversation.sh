#!/bin/bash
# Enhanced global hook to log Claude Code conversation events
# Handles multiple concurrent Claude instances by using unique session IDs
# Logs tool parameters, outputs, and Claude responses

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
    TOOL_INPUT=$(echo "$INPUT" | jq -c '.tool_input // {}')
    TOOL_RESPONSE=$(echo "$INPUT" | jq -c '.tool_response // {}')
    TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // ""')
else
    EVENT="unknown"
    CWD=$(pwd)
    SESSION_ID=""
    TOOL_INPUT="{}"
    TOOL_RESPONSE="{}"
fi

# Create unique log file per session
if [ -n "$SESSION_ID" ]; then
    SHORT_SESSION="${SESSION_ID:0:8}"
    LOG_FILE="$LOG_DIR/${DATE}-session-${SHORT_SESSION}.md"
else
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
            # Extract useful info based on tool type
            case "$TOOL" in
                Read)
                    FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // "unknown"')
                    echo "### [$TIMESTAMP] Tool: \`Read\` - \`$FILE_PATH\`" >> "$LOG_FILE"
                    ;;
                Write)
                    FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // "unknown"')
                    CONTENT_PREVIEW=$(echo "$TOOL_INPUT" | jq -r '.content // ""' | head -c 100)
                    echo "### [$TIMESTAMP] Tool: \`Write\` - \`$FILE_PATH\`" >> "$LOG_FILE"
                    if [ -n "$CONTENT_PREVIEW" ]; then
                        echo "<details><summary>Preview</summary>" >> "$LOG_FILE"
                        echo "" >> "$LOG_FILE"
                        echo "\`\`\`" >> "$LOG_FILE"
                        echo "$CONTENT_PREVIEW..." >> "$LOG_FILE"
                        echo "\`\`\`" >> "$LOG_FILE"
                        echo "</details>" >> "$LOG_FILE"
                    fi
                    ;;
                Edit)
                    FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // "unknown"')
                    OLD_STRING=$(echo "$TOOL_INPUT" | jq -r '.old_string // ""' | head -c 50)
                    echo "### [$TIMESTAMP] Tool: \`Edit\` - \`$FILE_PATH\`" >> "$LOG_FILE"
                    if [ -n "$OLD_STRING" ]; then
                        echo "<details><summary>Changed</summary>" >> "$LOG_FILE"
                        echo "" >> "$LOG_FILE"
                        echo "Old: \`${OLD_STRING}...\`" >> "$LOG_FILE"
                        echo "</details>" >> "$LOG_FILE"
                    fi
                    ;;
                Bash)
                    COMMAND=$(echo "$TOOL_INPUT" | jq -r '.command // "unknown"')
                    echo "### [$TIMESTAMP] Tool: \`Bash\`" >> "$LOG_FILE"
                    echo "\`\`\`bash" >> "$LOG_FILE"
                    echo "$COMMAND" >> "$LOG_FILE"
                    echo "\`\`\`" >> "$LOG_FILE"
                    # Log output if available
                    OUTPUT=$(echo "$TOOL_RESPONSE" | jq -r '.output // ""' | head -n 10)
                    if [ -n "$OUTPUT" ]; then
                        echo "<details><summary>Output</summary>" >> "$LOG_FILE"
                        echo "" >> "$LOG_FILE"
                        echo "\`\`\`" >> "$LOG_FILE"
                        echo "$OUTPUT" >> "$LOG_FILE"
                        echo "\`\`\`" >> "$LOG_FILE"
                        echo "</details>" >> "$LOG_FILE"
                    fi
                    ;;
                Glob|Grep)
                    PATTERN=$(echo "$TOOL_INPUT" | jq -r '.pattern // "unknown"')
                    echo "### [$TIMESTAMP] Tool: \`$TOOL\` - pattern: \`$PATTERN\`" >> "$LOG_FILE"
                    ;;
                TodoWrite)
                    TODO_COUNT=$(echo "$TOOL_INPUT" | jq '.todos | length')
                    echo "### [$TIMESTAMP] Tool: \`TodoWrite\` - $TODO_COUNT tasks" >> "$LOG_FILE"
                    # List todos
                    TODOS=$(echo "$TOOL_INPUT" | jq -r '.todos[] | "- [\(.status | if . == "completed" then "x" elif . == "in_progress" then ">" else " " end)] \(.content)"')
                    if [ -n "$TODOS" ]; then
                        echo "<details><summary>Tasks</summary>" >> "$LOG_FILE"
                        echo "" >> "$LOG_FILE"
                        echo "$TODOS" >> "$LOG_FILE"
                        echo "</details>" >> "$LOG_FILE"
                    fi
                    ;;
                Task)
                    SUBAGENT=$(echo "$TOOL_INPUT" | jq -r '.subagent_type // "unknown"')
                    TASK_PROMPT=$(echo "$TOOL_INPUT" | jq -r '.prompt // ""' | head -c 80)
                    echo "### [$TIMESTAMP] Tool: \`Task\` - \`$SUBAGENT\`" >> "$LOG_FILE"
                    if [ -n "$TASK_PROMPT" ]; then
                        echo "> ${TASK_PROMPT}..." >> "$LOG_FILE"
                    fi
                    ;;
                WebSearch)
                    QUERY=$(echo "$TOOL_INPUT" | jq -r '.query // "unknown"')
                    echo "### [$TIMESTAMP] Tool: \`WebSearch\` - \`$QUERY\`" >> "$LOG_FILE"
                    ;;
                WebFetch)
                    URL=$(echo "$TOOL_INPUT" | jq -r '.url // "unknown"')
                    echo "### [$TIMESTAMP] Tool: \`WebFetch\` - \`$URL\`" >> "$LOG_FILE"
                    ;;
                AskUserQuestion)
                    QUESTION=$(echo "$TOOL_INPUT" | jq -r '.questions[0].question // "unknown"')
                    echo "### [$TIMESTAMP] Tool: \`AskUserQuestion\`" >> "$LOG_FILE"
                    echo "> $QUESTION" >> "$LOG_FILE"
                    ;;
                *)
                    echo "### [$TIMESTAMP] Tool: \`$TOOL\`" >> "$LOG_FILE"
                    ;;
            esac
            echo "" >> "$LOG_FILE"
        fi
        ;;

    Stop)
        # Extract Claude's last response from transcript
        if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
            # Get the last assistant message from the transcript
            LAST_RESPONSE=$(tail -20 "$TRANSCRIPT_PATH" | jq -r 'select(.role == "assistant") | .content[] | select(.type == "text") | .text' 2>/dev/null | tail -c 500)

            echo "### [$TIMESTAMP] Claude Response" >> "$LOG_FILE"
            if [ -n "$LAST_RESPONSE" ]; then
                echo "<details><summary>Response excerpt</summary>" >> "$LOG_FILE"
                echo "" >> "$LOG_FILE"
                echo "$LAST_RESPONSE" >> "$LOG_FILE"
                echo "</details>" >> "$LOG_FILE"
            fi
            echo "" >> "$LOG_FILE"
        else
            echo "### [$TIMESTAMP] Response Complete" >> "$LOG_FILE"
            echo "" >> "$LOG_FILE"
        fi
        ;;
esac

exit 0
