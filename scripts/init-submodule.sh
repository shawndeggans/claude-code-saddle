#!/usr/bin/env bash
# Initialize project as git submodule
#
# Usage: ./scripts/init-submodule.sh <repo-url> [branch]
#
# This script adds an external repository as a git submodule in project/,
# allowing you to track upstream changes while keeping saddle separate.

set -euo pipefail

show_help() {
    cat << 'EOF'
Initialize project as git submodule

Usage: ./scripts/init-submodule.sh <repo-url> [branch]

Arguments:
    repo-url    Git repository URL (SSH or HTTPS)
    branch      Branch to track (default: main)

Examples:
    ./scripts/init-submodule.sh git@github.com:org/repo.git
    ./scripts/init-submodule.sh https://github.com/org/repo.git develop

This script:
    1. Adds the repository as a git submodule in project/
    2. Copies project-claude.md template to project/CLAUDE.md
    3. Runs initial index generation

Why submodules?
    - Keeps client code as separate git history
    - Useful for repos you don't own
    - Easy to track upstream changes
    - Clean separation of saddle and project commits
EOF
}

if [ $# -lt 1 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

REPO_URL="$1"
BRANCH="${2:-main}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

echo "=== Adding Project as Submodule ==="
echo "Repository: $REPO_URL"
echo "Branch: $BRANCH"
echo ""

# Check if project directory has content
if [ -d project ] && [ "$(ls -A project 2>/dev/null | grep -v .gitkeep)" ]; then
    echo "Warning: project/ directory is not empty"
    read -p "Remove existing contents and add submodule? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove contents but keep directory
        find project -mindepth 1 -delete 2>/dev/null || rm -rf project/*
    else
        echo "Aborted"
        exit 1
    fi
fi

# Remove project directory if it exists (git submodule add needs it empty)
rmdir project 2>/dev/null || true

# Add submodule
echo "Adding submodule..."
git submodule add -b "$BRANCH" "$REPO_URL" project

# Initialize submodule
git submodule update --init --recursive

# Copy template
if [ -f saddle/templates/project-claude.md ] && [ ! -f project/CLAUDE.md ]; then
    echo "Creating project/CLAUDE.md from template..."
    cp saddle/templates/project-claude.md project/CLAUDE.md
    echo "  Edit project/CLAUDE.md to add project-specific context"
fi

# Generate index
if [ -f saddle/index/generator/index_generator.py ]; then
    echo ""
    echo "Generating codebase index..."
    python3 saddle/index/generator/index_generator.py --full --verbose
fi

echo ""
echo "=== Submodule Setup Complete ==="
echo ""
echo "Submodule workflow:"
echo "  - Update submodule:  cd project && git pull"
echo "  - Commit submodule:  git add project && git commit"
echo "  - View submodule:    git submodule status"
echo ""
echo "Next steps:"
echo "  1. Edit project/CLAUDE.md with project-specific details"
echo "  2. Run './scripts/generate-index.sh' to refresh index"
