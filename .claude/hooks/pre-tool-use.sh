#!/usr/bin/env bash
# Pre-tool-use hook for Claude Code Saddle
#
# Purpose: Advisory TDD check before file writes (opt-in per project)
#
# This hook is ADVISORY ONLY - it informs but never blocks.
# TDD is disabled by default. Enable per-project in project/CLAUDE.md:
#   ## Enforcement
#   TDD: enabled
#
# Exit codes: Always 0 (advisory only)

set -euo pipefail

# Get the repository root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Check if TDD is enabled for this project
PROJECT_CLAUDE="$REPO_ROOT/project/CLAUDE.md"
TDD_ENABLED="false"
if [ -f "$PROJECT_CLAUDE" ] && grep -qE "^TDD:\s*enabled" "$PROJECT_CLAUDE" 2>/dev/null; then
    TDD_ENABLED="true"
fi

# Skip if TDD not enabled
if [ "$TDD_ENABLED" = "false" ]; then
    exit 0
fi

# Read tool input from stdin (Claude provides JSON)
TOOL_INPUT=$(cat)

# Extract file path from JSON input
FILE_PATH=$(echo "$TOOL_INPUT" | python3 -c "
import sys
import json

try:
    data = json.load(sys.stdin)
    tool_input = data.get('tool_input', {})
    path = tool_input.get('file_path') or tool_input.get('path') or ''
    print(path)
except Exception:
    print('')
" 2>/dev/null || echo "")

# Skip if no file path
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Skip files outside project/ directory
if [[ ! "$FILE_PATH" =~ ^project/ ]] && [[ ! "$FILE_PATH" =~ /project/ ]]; then
    exit 0
fi

# Skip test files
if [[ "$FILE_PATH" =~ test_ ]] || [[ "$FILE_PATH" =~ _test\.py$ ]] || [[ "$FILE_PATH" =~ \.test\.(js|ts)$ ]] || [[ "$FILE_PATH" =~ \.spec\.(js|ts)$ ]]; then
    exit 0
fi

# Skip if TDD Guard doesn't exist
TDD_GUARD="$REPO_ROOT/saddle/workflows/tdd-guard/tdd_guard.py"
if [ ! -f "$TDD_GUARD" ]; then
    exit 0
fi

# Run TDD Guard (advisory output only)
RESULT=$(python3 "$TDD_GUARD" "$FILE_PATH" "write" --json 2>&1 || true)

# Parse result and output advisory message if needed
echo "$RESULT" | python3 -c "
import sys
import json

try:
    data = json.load(sys.stdin)
    action = data.get('action', 'allow')
    message = data.get('message', '')
    guidance = data.get('guidance', '')

    if action in ('block', 'warn'):
        print('[TDD ADVISORY] ' + message)
        if guidance:
            print('  Suggestion: ' + guidance)
except Exception:
    pass
" 2>/dev/null || true

# Always exit 0 - advisory only
exit 0
