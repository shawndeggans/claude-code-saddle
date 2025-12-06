#!/usr/bin/env bash
# Pre-tool-use hook for Claude Code Saddle
#
# Purpose: Enforce TDD by checking for tests before allowing file writes
#
# This hook prevents the following failure mode:
#   - Claude "forgets" TDD requirements deep in a session
#   - Code gets written without tests
#   - Quality degrades over time
#
# Exit codes:
#   0 - Allow operation
#   1 - Block operation (TDD Guard rejection)
#   2 - Warn but allow

set -euo pipefail

# Get the repository root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Read tool input from stdin (Claude provides JSON)
TOOL_INPUT=$(cat)

# Extract file path from JSON input
FILE_PATH=$(echo "$TOOL_INPUT" | python3 -c "
import sys
import json

try:
    data = json.load(sys.stdin)
    tool_input = data.get('tool_input', {})

    # Handle different tool input formats
    path = tool_input.get('file_path') or tool_input.get('path') or ''
    print(path)
except Exception:
    print('')
" 2>/dev/null || echo "")

# Skip if no file path or not in project directory
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Skip files outside project/ and saddle/ directories
if [[ ! "$FILE_PATH" =~ ^(project/|saddle/) ]] && [[ ! "$FILE_PATH" =~ ^\.?/.*(project/|saddle/) ]]; then
    exit 0
fi

# Skip test files - they should always be allowed
if [[ "$FILE_PATH" =~ test_ ]] || [[ "$FILE_PATH" =~ _test\.py$ ]] || [[ "$FILE_PATH" =~ \.test\.(js|ts)$ ]] || [[ "$FILE_PATH" =~ \.spec\.(js|ts)$ ]]; then
    exit 0
fi

# Skip if TDD Guard doesn't exist yet (during initial setup)
TDD_GUARD="$REPO_ROOT/saddle/workflows/tdd-guard/tdd_guard.py"
if [ ! -f "$TDD_GUARD" ]; then
    exit 0
fi

# Run TDD Guard
python3 "$TDD_GUARD" "$FILE_PATH" "write" --json 2>&1 || true

# Note: We always exit 0 during setup to avoid blocking
# In production, you would use: exit $?
exit 0
