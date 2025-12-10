#!/usr/bin/env bash
# Session start hook for Claude Code Saddle
# Purpose: Minimal context refresh on session start

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo "Saddle active. Index: saddle/index/CODEBASE.md"
echo ""

# Show brief git status
if git rev-parse --is-inside-work-tree &>/dev/null; then
    CHANGES=$(git status --porcelain 2>/dev/null | wc -l || echo "0")
    if [ "$CHANGES" -gt 0 ]; then
        echo "Uncommitted changes:"
        git status --short 2>/dev/null | head -5
        [ "$CHANGES" -gt 5 ] && echo "  ... and $((CHANGES - 5)) more"
    else
        echo "Working tree clean"
    fi
fi
