#!/usr/bin/env bash
# Claude Code Saddle Setup Script
#
# Usage: ./scripts/setup.sh [--skip-venv] [--skip-hooks]
#
# This script sets up the saddle environment including:
#   - Python virtual environment
#   - Dependencies from pyproject.toml
#   - Pre-commit hooks
#   - Initial directory structure

set -euo pipefail

show_help() {
    cat << 'EOF'
Claude Code Saddle Setup

Usage: ./scripts/setup.sh [OPTIONS]

Options:
    --skip-venv     Skip virtual environment creation
    --skip-hooks    Skip pre-commit hook installation
    --help, -h      Show this help message

This script:
    1. Creates a Python virtual environment (.venv)
    2. Installs dependencies from pyproject.toml
    3. Installs pre-commit hooks
    4. Initializes saddle directories
    5. Generates initial codebase index
EOF
}

SKIP_VENV=false
SKIP_HOOKS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-venv) SKIP_VENV=true; shift ;;
        --skip-hooks) SKIP_HOOKS=true; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) echo "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

echo "=== Claude Code Saddle Setup ==="
echo ""

# Step 1: Virtual environment
if [ "$SKIP_VENV" = false ]; then
    echo "Step 1: Creating virtual environment..."
    python3 -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    echo "  Virtual environment created at .venv"
else
    echo "Step 1: Skipping virtual environment creation"
    if [ -f .venv/bin/activate ]; then
        # shellcheck disable=SC1091
        source .venv/bin/activate
    fi
fi

# Step 2: Install dependencies
echo ""
echo "Step 2: Installing dependencies..."
pip install --upgrade pip -q
pip install -e ".[dev]" -q
echo "  Dependencies installed"

# Step 3: Pre-commit hooks
if [ "$SKIP_HOOKS" = false ]; then
    echo ""
    echo "Step 3: Installing pre-commit hooks..."
    pre-commit install
    echo "  Pre-commit hooks installed"
else
    echo ""
    echo "Step 3: Skipping pre-commit hook installation"
fi

# Step 4: Initialize directories
echo ""
echo "Step 4: Initializing directories..."
mkdir -p saddle/index
mkdir -p saddle/cleanup
mkdir -p saddle/workflows/tdd-guard
mkdir -p saddle/workflows/doc-verify/templates
mkdir -p saddle/rules
mkdir -p saddle/templates
mkdir -p .claude/hooks
mkdir -p project/src
mkdir -p project/tests
echo "  Directories initialized"

# Step 5: Make hook scripts executable
echo ""
echo "Step 5: Setting permissions..."
chmod +x .claude/hooks/*.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true
echo "  Permissions set"

# Step 6: Generate initial index (if project has files)
echo ""
echo "Step 6: Generating initial codebase index..."
if [ -f saddle/index/generator/index_generator.py ]; then
    python3 saddle/index/generator/index_generator.py --full --verbose || echo "  No project files to index yet"
else
    echo "  Index generator not ready yet"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Add your project code:"
echo "     ./scripts/init-submodule.sh <repo-url>   # For external repos"
echo "     ./scripts/init-nested.sh [source-path]   # For local code"
echo ""
echo "  3. Review and customize CLAUDE.md for your needs"
echo ""
echo "  4. Run './scripts/generate-index.sh' after adding project code"
