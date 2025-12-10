#!/usr/bin/env bash
# Claude Code Saddle Setup
#
# Usage: ./scripts/setup.sh
#
# Single command setup - creates venv, installs deps, configures hooks.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

echo "Setting up Claude Code Saddle..."

# Create virtual environment
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

# Install dependencies quietly
pip install --upgrade pip -q
pip install -e ".[dev]" -q

# Install pre-commit hooks (both pre-commit and post-commit for auto-indexing)
pre-commit install --hook-type pre-commit --hook-type post-commit

# Make scripts executable
chmod +x .claude/hooks/*.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

# Generate initial index if possible
if [ -f saddle/index/generator/index_generator.py ]; then
    python3 saddle/index/generator/index_generator.py --full 2>/dev/null || true
fi

echo ""
echo "Ready. Add code to project/, then commit to trigger auto-indexing."
echo "Activate environment: source .venv/bin/activate"
