#!/usr/bin/env bash
# Session start hook for Claude Code Saddle
#
# Purpose: Refresh context on session start/resume
#
# This hook prevents the following failure mode:
#   - New session starts without context
#   - Agent doesn't know project state
#   - Wastes time re-exploring
#
# This script outputs key information that Claude should be aware of
# at the start of each session.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo "=== Claude Code Saddle Session Start ==="
echo ""
echo "Repository: $(basename "$REPO_ROOT")"
echo "Date: $(date '+%Y-%m-%d %H:%M')"
echo ""

# Show key rules
RULES_FILE="$REPO_ROOT/saddle/rules/universal.md"
if [ -f "$RULES_FILE" ]; then
    echo "--- Key Rules ---"
    head -30 "$RULES_FILE" | grep -E "^-|^#|NEVER|ALWAYS" || true
    echo ""
fi

# Show codebase summary (first 50 lines)
CODEBASE_FILE="$REPO_ROOT/saddle/index/CODEBASE.md"
if [ -f "$CODEBASE_FILE" ]; then
    echo "--- Codebase Summary ---"
    head -50 "$CODEBASE_FILE"
    echo ""
    echo "[See full index: saddle/index/CODEBASE.md]"
    echo ""
fi

# Show current todo state
TODO_FILE="$REPO_ROOT/saddle/templates/todo.md"
if [ -f "$TODO_FILE" ]; then
    # Check if it has content beyond template
    if grep -q "Not Started\|In Progress\|Blocked" "$TODO_FILE" 2>/dev/null; then
        echo "--- Current TODO ---"
        head -30 "$TODO_FILE"
        echo ""
    fi
fi

# Status check
echo "--- Status Check ---"

# Check for uncommitted changes
CHANGES=$(git status --porcelain 2>/dev/null | wc -l || echo "0")
if [ "$CHANGES" -gt 0 ]; then
    echo "Uncommitted changes: $CHANGES files"
    git status --porcelain | head -10
    echo ""
fi

# Check index freshness
INDEX_FILE="$REPO_ROOT/saddle/index/codebase-index.json"
if [ -f "$INDEX_FILE" ]; then
    # Check if older than 24 hours
    if [ "$(find "$INDEX_FILE" -mmin +1440 2>/dev/null)" ]; then
        echo "WARNING: Codebase index is over 24 hours old."
        echo "Run: ./scripts/generate-index.sh"
        echo ""
    fi
fi

# Check for failing tests (quick check)
if [ -d "$REPO_ROOT/project/tests" ]; then
    echo "Test directory: project/tests/ (run pytest to verify)"
fi

echo ""
echo "=== Ready ==="
echo ""
echo "Commands:"
echo "  /index   - Regenerate codebase index"
echo "  /cleanup - Run dead code detection"
echo "  /todo    - Show current session state"
