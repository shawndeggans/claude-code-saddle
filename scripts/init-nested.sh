#!/usr/bin/env bash
# Initialize project as nested folder
#
# Usage: ./scripts/init-nested.sh [source-path]
#
# This script either copies existing code into project/ or creates
# an empty project structure for new development.

set -euo pipefail

show_help() {
    cat << 'EOF'
Initialize project as nested folder

Usage: ./scripts/init-nested.sh [source-path]

Arguments:
    source-path    Optional path to existing code to copy

Examples:
    ./scripts/init-nested.sh                    # Create empty structure
    ./scripts/init-nested.sh ../my-app          # Copy from local path
    ./scripts/init-nested.sh ~/projects/client  # Copy from absolute path

This script:
    1. If source-path provided: copies code into project/
    2. If no source-path: creates empty project structure
    3. Initializes project/CLAUDE.md from template
    4. Runs initial index generation

Why nested folders?
    - Simplifies workflow when starting new projects
    - Useful when modifying code heavily
    - Single-repo delivery for clients
    - All code in one git history
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    show_help
    exit 0
fi

SOURCE_PATH="${1:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

echo "=== Initializing Nested Project ==="
echo ""

# Ensure project directory exists
mkdir -p project

if [ -n "$SOURCE_PATH" ]; then
    # Copy from source
    if [ ! -d "$SOURCE_PATH" ]; then
        echo "Error: Source path does not exist: $SOURCE_PATH"
        exit 1
    fi

    echo "Copying from: $SOURCE_PATH"

    # Check if project has content
    if [ "$(ls -A project 2>/dev/null | grep -v .gitkeep | grep -v CLAUDE.md)" ]; then
        read -p "project/ has content. Overwrite? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted"
            exit 1
        fi
    fi

    # Copy contents (preserving structure)
    cp -r "$SOURCE_PATH"/* project/ 2>/dev/null || true
    cp -r "$SOURCE_PATH"/.[!.]* project/ 2>/dev/null || true

    echo "  Copied $(find project -type f | wc -l) files"
else
    # Create empty structure
    echo "Creating empty project structure..."

    mkdir -p project/src
    mkdir -p project/tests
    mkdir -p project/config

    # Create placeholder files
    touch project/src/__init__.py
    touch project/tests/__init__.py

    # Create a simple main.py
    if [ ! -f project/src/main.py ]; then
        cat > project/src/main.py << 'PYEOF'
"""Main entry point for the application."""


def main() -> None:
    """Application entry point."""
    print("Hello from your new project!")


if __name__ == "__main__":
    main()
PYEOF
    fi

    # Create a simple test
    if [ ! -f project/tests/test_main.py ]; then
        cat > project/tests/test_main.py << 'PYEOF'
"""Tests for main module."""

from project.src.main import main


def test_main_runs() -> None:
    """Test that main function runs without error."""
    # This is a placeholder test
    main()
PYEOF
    fi

    echo "  Created project structure"
fi

# Copy template if CLAUDE.md doesn't exist
if [ -f saddle/templates/project-claude.md ] && [ ! -f project/CLAUDE.md ]; then
    echo ""
    echo "Creating project/CLAUDE.md from template..."
    cp saddle/templates/project-claude.md project/CLAUDE.md
fi

# Generate index
if [ -f saddle/index/generator/index_generator.py ]; then
    echo ""
    echo "Generating codebase index..."
    python3 saddle/index/generator/index_generator.py --full --verbose || echo "  Index generation skipped"
fi

echo ""
echo "=== Nested Project Setup Complete ==="
echo ""
echo "Project structure:"
find project -type f -name "*.py" | head -10
echo ""
echo "Next steps:"
echo "  1. Add your code to project/src/"
echo "  2. Edit project/CLAUDE.md with project-specific details"
echo "  3. Run './scripts/generate-index.sh' after adding code"
