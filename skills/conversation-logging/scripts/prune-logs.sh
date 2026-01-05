#!/bin/bash
# Prune old conversation logs
# Default: Delete logs older than 14 days

set -e

LOG_DIR="$HOME/.claude/conversation-logs"
DEFAULT_DAYS=14
DAYS=${1:-$DEFAULT_DAYS}
DRY_RUN=${2:-}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ ! -d "$LOG_DIR" ]; then
    echo -e "${YELLOW}No conversation logs directory found at $LOG_DIR${NC}"
    exit 0
fi

# Count logs to be deleted
OLD_LOGS=$(find "$LOG_DIR" -name "*.md" -type f -mtime +$DAYS 2>/dev/null)
COUNT=$(echo "$OLD_LOGS" | grep -c "\.md$" || true)

if [ "$COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ No logs older than $DAYS days found${NC}"
    exit 0
fi

# Calculate size
TOTAL_SIZE=$(find "$LOG_DIR" -name "*.md" -type f -mtime +$DAYS -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1 || echo "unknown")

echo -e "${YELLOW}Found $COUNT log file(s) older than $DAYS days (total size: $TOTAL_SIZE)${NC}"
echo ""

# Show what will be deleted
echo "Logs to be removed:"
find "$LOG_DIR" -name "*.md" -type f -mtime +$DAYS -printf "  - %f (modified: %TY-%Tm-%Td)\n" 2>/dev/null | head -20

if [ "$COUNT" -gt 20 ]; then
    echo "  ... and $((COUNT - 20)) more"
fi
echo ""

# Dry run check
if [ "$DRY_RUN" = "--dry-run" ] || [ "$DRY_RUN" = "-n" ]; then
    echo -e "${YELLOW}Dry run - no files deleted${NC}"
    exit 0
fi

# Confirm deletion
read -p "Delete these $COUNT log file(s)? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled - no files deleted${NC}"
    exit 0
fi

# Delete logs
DELETED=$(find "$LOG_DIR" -name "*.md" -type f -mtime +$DAYS -delete -print 2>/dev/null | wc -l)

echo -e "${GREEN}✓ Deleted $DELETED log file(s) older than $DAYS days${NC}"
echo -e "${GREEN}✓ Freed up $TOTAL_SIZE of disk space${NC}"
