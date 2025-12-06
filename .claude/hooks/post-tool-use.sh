#!/usr/bin/env bash
# Post-tool-use hook for Claude Code Saddle
#
# Purpose: Verify documentation after file modifications
#
# This hook prevents the following failure mode:
#   - Code is written/modified
#   - Documentation is not updated
#   - Knowledge gap accumulates
#
# Also: Updates audit trail for session tracking

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Read tool input from stdin
TOOL_INPUT=$(cat)

# Extract file path
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

# Skip if no file path or not a Python file
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

if [[ ! "$FILE_PATH" == *.py ]]; then
    exit 0
fi

# Skip test files
if [[ "$FILE_PATH" =~ test_ ]] || [[ "$FILE_PATH" =~ _test\.py$ ]]; then
    exit 0
fi

# Run documentation verification (warn only, don't block)
DOC_VERIFY="$REPO_ROOT/saddle/workflows/doc-verify/doc_verify.py"
if [ -f "$DOC_VERIFY" ]; then
    python3 "$DOC_VERIFY" --files "$FILE_PATH" --format text 2>&1 || true
fi

# Log to session audit trail
SESSION_LOG="$REPO_ROOT/.session-log.txt"
echo "$(date -Iseconds) - Modified: $FILE_PATH" >> "$SESSION_LOG" 2>/dev/null || true

exit 0
