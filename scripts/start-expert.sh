#!/bin/bash
#
# Start an expert's MCP server
#
# Usage: ./scripts/start-expert.sh <expert-name> [--background]
#
# Example:
#   ./scripts/start-expert.sh databricks
#   ./scripts/start-expert.sh databricks --background
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SADDLE_ROOT="$(dirname "$SCRIPT_DIR")"
EXPERTS_DIR="$SADDLE_ROOT/saddle/experts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 <expert-name> [--background]"
    echo ""
    echo "Arguments:"
    echo "  expert-name    Name of the expert to start"
    echo "  --background   Run server in background"
    echo ""
    echo "Example:"
    echo "  $0 databricks"
    echo "  $0 databricks --background"
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

EXPERT_NAME="$1"
BACKGROUND=false

if [ "$2" = "--background" ]; then
    BACKGROUND=true
fi

EXPERT_DIR="$EXPERTS_DIR/$EXPERT_NAME"
SERVER_PATH="$EXPERT_DIR/mcp-server/server.py"
CONFIG_PATH="$EXPERT_DIR/mcp-server/config.yaml"
REQUIREMENTS_PATH="$EXPERT_DIR/mcp-server/requirements.txt"

# Check if expert exists
if [ ! -d "$EXPERT_DIR" ]; then
    echo -e "${RED}Error: Expert '$EXPERT_NAME' not found${NC}"
    echo "Available experts:"
    ls -1 "$EXPERTS_DIR" 2>/dev/null | grep -v "^_" | grep -v "README" | grep -v "EXPERT-TEMPLATE" || echo "  (none)"
    exit 1
fi

# Check if server.py exists
if [ ! -f "$SERVER_PATH" ]; then
    echo -e "${RED}Error: Server not found at $SERVER_PATH${NC}"
    exit 1
fi

# Check if config exists
if [ ! -f "$CONFIG_PATH" ]; then
    echo -e "${RED}Error: Config not found at $CONFIG_PATH${NC}"
    exit 1
fi

# Extract port from config
PORT=$(grep -A1 "^server:" "$CONFIG_PATH" | grep "port:" | sed 's/.*port: *//')
if [ -z "$PORT" ]; then
    PORT="8100"
fi

echo -e "${GREEN}Starting $EXPERT_NAME expert...${NC}"
echo "Server: $SERVER_PATH"
echo "Port: $PORT"
echo ""

# Check if port is already in use
if lsof -i ":$PORT" > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port $PORT appears to be in use${NC}"
    echo "Existing process:"
    lsof -i ":$PORT" | head -2
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Activate virtual environment if it exists
if [ -f "$SADDLE_ROOT/.venv/bin/activate" ]; then
    source "$SADDLE_ROOT/.venv/bin/activate"
fi

# Install requirements if needed
if [ -f "$REQUIREMENTS_PATH" ]; then
    echo "Checking dependencies..."
    pip install -q -r "$REQUIREMENTS_PATH" 2>/dev/null || {
        echo -e "${YELLOW}Warning: Could not install dependencies${NC}"
        echo "Run: pip install -r $REQUIREMENTS_PATH"
    }
fi

# Change to expert directory for relative path resolution
cd "$EXPERT_DIR"

if [ "$BACKGROUND" = true ]; then
    # Run in background
    LOG_FILE="$EXPERT_DIR/server.log"
    PID_FILE="$EXPERT_DIR/server.pid"

    echo "Starting in background..."
    nohup python "$SERVER_PATH" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    echo -e "${GREEN}Server started in background${NC}"
    echo "PID: $(cat "$PID_FILE")"
    echo "Log: $LOG_FILE"
    echo ""
    echo "To stop: kill \$(cat $PID_FILE)"
else
    # Run in foreground
    echo "Starting in foreground (Ctrl+C to stop)..."
    echo ""
    python "$SERVER_PATH"
fi
