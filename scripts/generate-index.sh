#!/usr/bin/env bash
# Trigger codebase index regeneration
#
# Usage: ./scripts/generate-index.sh [--full|--incremental]
#
# Generates the following files in saddle/index/:
#   - codebase-index.json: File/function/class map
#   - dependency-graph.json: Import relationships
#   - stale-files.json: Archival candidates
#   - CODEBASE.md: Human-readable summary

set -euo pipefail

show_help() {
    cat << 'EOF'
Generate codebase index

Usage: ./scripts/generate-index.sh [OPTIONS]

Options:
    --full          Complete rebuild of all indexes
    --incremental   Only reindex changed files (default)
    --verbose, -v   Show detailed progress
    --help, -h      Show this help message

Generates:
    - saddle/index/codebase-index.json
    - saddle/index/dependency-graph.json
    - saddle/index/stale-files.json
    - saddle/index/CODEBASE.md

Examples:
    ./scripts/generate-index.sh                # Incremental update
    ./scripts/generate-index.sh --full         # Complete rebuild
    ./scripts/generate-index.sh --full -v      # Verbose full rebuild
EOF
}

MODE="--incremental"
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --full) MODE="--full"; shift ;;
        --incremental) MODE="--incremental"; shift ;;
        -v|--verbose) VERBOSE="--verbose"; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) echo "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

# Activate venv if available
if [ -f .venv/bin/activate ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

echo "=== Generating Codebase Index ==="
echo "Mode: ${MODE#--}"
echo ""

INDEX_GENERATOR="saddle/index/generator/index_generator.py"

if [ ! -f "$INDEX_GENERATOR" ]; then
    echo "Error: Index generator not found"
    echo "Expected: $INDEX_GENERATOR"
    exit 1
fi

# Check if project directory has content
if [ ! -d project ] || [ -z "$(find project -name '*.py' 2>/dev/null | head -1)" ]; then
    echo "Warning: No Python files found in project/"
    echo "Add code first, then run this script again."
    exit 0
fi

# Run the generator
# shellcheck disable=SC2086
python3 "$INDEX_GENERATOR" $MODE $VERBOSE

echo ""
echo "=== Index Generation Complete ==="
echo ""
echo "Generated files:"
ls -la saddle/index/*.json saddle/index/*.md 2>/dev/null | awk '{print "  " $NF " (" $5 " bytes)"}'
