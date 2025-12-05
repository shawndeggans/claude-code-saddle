#!/usr/bin/env bash
# Execute cleanup analysis
#
# Usage: ./scripts/run-cleanup.sh [--report|--fix]
#
# Analyzes the codebase for:
#   - Dead code (unused functions, classes, imports)
#   - Stale files (not modified in 6+ months)
#   - Orphaned configuration files

set -euo pipefail

show_help() {
    cat << 'EOF'
Run cleanup analysis

Usage: ./scripts/run-cleanup.sh [OPTIONS]

Options:
    --report        Output findings only (default)
    --fix           Apply safe auto-fixes (with confirmation)
    --dead-code     Only run dead code detection
    --stale-files   Only run stale file tracking
    --format        Output format: text, json, markdown (default: text)
    --help, -h      Show this help message

Analyzes:
    - Dead code via vulture and deadcode
    - Stale files via git history
    - Orphaned configuration files

Examples:
    ./scripts/run-cleanup.sh                    # Full report
    ./scripts/run-cleanup.sh --dead-code        # Only dead code
    ./scripts/run-cleanup.sh --format markdown  # Markdown output
EOF
}

MODE="report"
RUN_DEAD_CODE=true
RUN_STALE=true
FORMAT="text"

while [[ $# -gt 0 ]]; do
    case $1 in
        --report) MODE="report"; shift ;;
        --fix) MODE="fix"; shift ;;
        --dead-code) RUN_STALE=false; shift ;;
        --stale-files) RUN_DEAD_CODE=false; shift ;;
        --format) FORMAT="$2"; shift 2 ;;
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

echo "=== Running Cleanup Analysis ==="
echo ""

# Check if project exists
if [ ! -d project ]; then
    echo "Error: project/ directory not found"
    exit 1
fi

DEAD_CODE_DETECTOR="saddle/cleanup/dead_code_detector.py"
STALE_TRACKER="saddle/cleanup/stale_file_tracker.py"

if [ "$RUN_DEAD_CODE" = true ]; then
    echo "--- Dead Code Detection ---"
    echo ""

    if [ -f "$DEAD_CODE_DETECTOR" ]; then
        if [ "$MODE" = "fix" ]; then
            python3 "$DEAD_CODE_DETECTOR" project/ --fix
        else
            python3 "$DEAD_CODE_DETECTOR" project/ --format "$FORMAT"
        fi
    else
        # Fallback to direct vulture
        echo "Using vulture directly (detector not found)..."
        vulture project/ --min-confidence 80 || true
    fi

    echo ""
fi

if [ "$RUN_STALE" = true ]; then
    echo "--- Stale File Tracking ---"
    echo ""

    if [ -f "$STALE_TRACKER" ]; then
        python3 "$STALE_TRACKER" project/ --format "$FORMAT"
    else
        echo "Stale file tracker not found: $STALE_TRACKER"
        echo ""
        echo "Checking for old files manually..."
        echo "Files not modified in 180+ days:"
        find project -name "*.py" -mtime +180 2>/dev/null | head -10 || echo "  None found"
    fi

    echo ""
fi

echo "=== Cleanup Analysis Complete ==="
echo ""
echo "To archive stale files:"
echo "  python3 saddle/cleanup/archive_manager.py archive <path>"
echo ""
echo "To view archive:"
echo "  python3 saddle/cleanup/archive_manager.py list"
