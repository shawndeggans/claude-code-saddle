#!/bin/bash
#
# Test an expert system before use
#
# Usage: ./scripts/test-expert.sh <expert-name> [options]
#
# Options:
#   --check-tokens    Only check token budget
#   --verbose         Show detailed output
#
# Example:
#   ./scripts/test-expert.sh databricks
#   ./scripts/test-expert.sh databricks --check-tokens
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SADDLE_ROOT="$(dirname "$SCRIPT_DIR")"
EXPERTS_DIR="$SADDLE_ROOT/saddle/experts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 <expert-name> [options]"
    echo ""
    echo "Arguments:"
    echo "  expert-name      Name of the expert to test"
    echo ""
    echo "Options:"
    echo "  --check-tokens   Only check token budget"
    echo "  --verbose        Show detailed output"
    echo ""
    echo "Example:"
    echo "  $0 databricks"
    echo "  $0 databricks --check-tokens"
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

EXPERT_NAME="$1"
CHECK_TOKENS_ONLY=false
VERBOSE=false

shift
while [ $# -gt 0 ]; do
    case "$1" in
        --check-tokens)
            CHECK_TOKENS_ONLY=true
            ;;
        --verbose)
            VERBOSE=true
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
    shift
done

EXPERT_DIR="$EXPERTS_DIR/$EXPERT_NAME"

# Check if expert exists
if [ ! -d "$EXPERT_DIR" ]; then
    echo -e "${RED}Error: Expert '$EXPERT_NAME' not found${NC}"
    echo "Available experts:"
    ls -1 "$EXPERTS_DIR" 2>/dev/null | grep -v "^_" | grep -v "README" | grep -v "EXPERT-TEMPLATE" || echo "  (none)"
    exit 1
fi

echo -e "${BLUE}Testing expert: $EXPERT_NAME${NC}"
echo "Location: $EXPERT_DIR"
echo ""

PASSED=0
FAILED=0
WARNED=0

# Helper functions
pass() {
    echo -e "${GREEN}PASS${NC}: $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}FAIL${NC}: $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}WARN${NC}: $1"
    ((WARNED++))
}

# Token counting function
count_tokens() {
    local file="$1"
    if [ -f "$file" ]; then
        # Approximate: 1 token ~ 4 characters
        local chars=$(wc -c < "$file")
        echo $((chars / 4))
    else
        echo 0
    fi
}

# Test 1: Check SKILL.md exists
echo -e "${BLUE}Checking knowledge files...${NC}"
if [ -f "$EXPERT_DIR/SKILL.md" ]; then
    pass "SKILL.md exists"

    # Check for placeholders
    if grep -q "{{EXPERT_NAME}}" "$EXPERT_DIR/SKILL.md"; then
        fail "SKILL.md still has placeholder values"
    else
        pass "SKILL.md customized"
    fi
else
    fail "SKILL.md not found"
fi

# Test 2: Check knowledge directories
KNOWLEDGE_DIRS=("core" "reference" "org-patterns" "decision-log")
for dir in "${KNOWLEDGE_DIRS[@]}"; do
    if [ -d "$EXPERT_DIR/knowledge/$dir" ]; then
        pass "knowledge/$dir/ exists"
    else
        fail "knowledge/$dir/ not found"
    fi
done

# Test 3: Check token budget
echo ""
echo -e "${BLUE}Checking token budget...${NC}"
TOTAL_TOKENS=0
MAX_TOKENS=4000

# Count SKILL.md tokens
SKILL_TOKENS=$(count_tokens "$EXPERT_DIR/SKILL.md")
TOTAL_TOKENS=$((TOTAL_TOKENS + SKILL_TOKENS))
[ "$VERBOSE" = true ] && echo "  SKILL.md: ~$SKILL_TOKENS tokens"

# Count core knowledge tokens
for file in "$EXPERT_DIR/knowledge/core"/*.md 2>/dev/null; do
    if [ -f "$file" ]; then
        FILE_TOKENS=$(count_tokens "$file")
        TOTAL_TOKENS=$((TOTAL_TOKENS + FILE_TOKENS))
        [ "$VERBOSE" = true ] && echo "  $(basename "$file"): ~$FILE_TOKENS tokens"
    fi
done

if [ $TOTAL_TOKENS -le $MAX_TOKENS ]; then
    pass "Core knowledge: ~$TOTAL_TOKENS tokens (max $MAX_TOKENS)"
else
    fail "Core knowledge: ~$TOTAL_TOKENS tokens exceeds max $MAX_TOKENS"
fi

if [ "$CHECK_TOKENS_ONLY" = true ]; then
    echo ""
    echo "Token check complete."
    exit 0
fi

# Test 4: Check configuration
echo ""
echo -e "${BLUE}Checking configuration...${NC}"
CONFIG_PATH="$EXPERT_DIR/mcp-server/config.yaml"

if [ -f "$CONFIG_PATH" ]; then
    pass "config.yaml exists"

    # Check for placeholders
    if grep -q "{{EXPERT_NAME}}" "$CONFIG_PATH" || grep -q "{{PORT}}" "$CONFIG_PATH"; then
        fail "config.yaml still has placeholder values"
    else
        pass "config.yaml customized"
    fi

    # Check port
    PORT=$(grep -A1 "^server:" "$CONFIG_PATH" | grep "port:" | sed 's/.*port: *//')
    if [ -n "$PORT" ] && [ "$PORT" -ge 1024 ] && [ "$PORT" -le 65535 ]; then
        pass "Port configured: $PORT"
    else
        fail "Invalid port configuration"
    fi
else
    fail "config.yaml not found"
fi

# Test 5: Check server module
echo ""
echo -e "${BLUE}Checking server module...${NC}"
SERVER_PATH="$EXPERT_DIR/mcp-server/server.py"

if [ -f "$SERVER_PATH" ]; then
    pass "server.py exists"

    # Check Python syntax
    if python -m py_compile "$SERVER_PATH" 2>/dev/null; then
        pass "server.py syntax valid"
    else
        fail "server.py has syntax errors"
    fi

    # Check for placeholders
    if grep -q "{{expert_name}}" "$SERVER_PATH"; then
        fail "server.py still has placeholder values"
    else
        pass "server.py customized"
    fi
else
    fail "server.py not found"
fi

# Test 6: Check requirements
REQUIREMENTS_PATH="$EXPERT_DIR/mcp-server/requirements.txt"
if [ -f "$REQUIREMENTS_PATH" ]; then
    pass "requirements.txt exists"
else
    warn "requirements.txt not found"
fi

# Test 7: Check README
echo ""
echo -e "${BLUE}Checking documentation...${NC}"
README_PATH="$EXPERT_DIR/README.md"

if [ -f "$README_PATH" ]; then
    pass "README.md exists"

    # Check for placeholders
    if grep -q "{{EXPERT_NAME}}" "$README_PATH"; then
        fail "README.md still has placeholder values"
    else
        pass "README.md customized"
    fi
else
    fail "README.md not found"
fi

# Test 8: Run pytest if available
echo ""
echo -e "${BLUE}Running unit tests...${NC}"
TESTS_PATH="$EXPERT_DIR/tests/test_expert.py"

if [ -f "$TESTS_PATH" ]; then
    if command -v pytest &> /dev/null; then
        # Activate venv if available
        if [ -f "$SADDLE_ROOT/.venv/bin/activate" ]; then
            source "$SADDLE_ROOT/.venv/bin/activate"
        fi

        if pytest "$TESTS_PATH" -v --tb=short 2>/dev/null; then
            pass "Unit tests passed"
        else
            fail "Unit tests failed"
        fi
    else
        warn "pytest not installed, skipping unit tests"
    fi
else
    warn "test_expert.py not found"
fi

# Summary
echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}Passed${NC}: $PASSED"
echo -e "${YELLOW}Warned${NC}: $WARNED"
echo -e "${RED}Failed${NC}: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}Expert '$EXPERT_NAME' is ready to use!${NC}"
    echo ""
    echo "Start with: ./scripts/start-expert.sh $EXPERT_NAME"
    exit 0
else
    echo -e "${RED}Expert '$EXPERT_NAME' has issues that need to be fixed.${NC}"
    exit 1
fi
