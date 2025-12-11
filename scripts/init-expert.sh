#!/bin/bash
#
# Initialize a new expert system from the template
#
# Usage: ./scripts/init-expert.sh <expert-name> [domain-description]
#
# Example:
#   ./scripts/init-expert.sh databricks "Databricks platform, Asset Bundles, and MLFlow"
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SADDLE_ROOT="$(dirname "$SCRIPT_DIR")"
EXPERTS_DIR="$SADDLE_ROOT/saddle/experts"
TEMPLATE_DIR="$EXPERTS_DIR/EXPERT-TEMPLATE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 <expert-name> [domain-description]"
    echo ""
    echo "Arguments:"
    echo "  expert-name         Name of the expert (lowercase, hyphenated)"
    echo "  domain-description  Description of the domain (optional)"
    echo ""
    echo "Example:"
    echo "  $0 databricks \"Databricks platform, Asset Bundles, and MLFlow\""
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

EXPERT_NAME="$1"
DOMAIN_DESCRIPTION="${2:-$EXPERT_NAME domain}"

# Validate expert name (lowercase, alphanumeric with hyphens)
if [[ ! "$EXPERT_NAME" =~ ^[a-z][a-z0-9-]*$ ]]; then
    echo -e "${RED}Error: Expert name must be lowercase, start with a letter, and contain only letters, numbers, and hyphens${NC}"
    exit 1
fi

EXPERT_DIR="$EXPERTS_DIR/$EXPERT_NAME"

# Check if expert already exists
if [ -d "$EXPERT_DIR" ]; then
    echo -e "${RED}Error: Expert '$EXPERT_NAME' already exists at $EXPERT_DIR${NC}"
    exit 1
fi

# Check if template exists
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo -e "${RED}Error: Template not found at $TEMPLATE_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}Creating expert: $EXPERT_NAME${NC}"
echo "Domain: $DOMAIN_DESCRIPTION"
echo ""

# Copy template to new expert directory
echo "Copying template..."
cp -r "$TEMPLATE_DIR" "$EXPERT_DIR"

# Generate unique port number (8100 + hash of expert name)
# This ensures consistent ports across runs for the same expert
PORT_BASE=8100
PORT_OFFSET=$(echo -n "$EXPERT_NAME" | cksum | cut -d' ' -f1)
PORT=$((PORT_BASE + (PORT_OFFSET % 100)))

# Create name variants for replacement
EXPERT_NAME_UPPER=$(echo "$EXPERT_NAME" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
EXPERT_NAME_SNAKE=$(echo "$EXPERT_NAME" | tr '-' '_')

echo "Customizing files..."

# Function to replace placeholders in a file
replace_placeholders() {
    local file="$1"
    if [ -f "$file" ]; then
        sed -i "s/{{EXPERT_NAME}}/$EXPERT_NAME/g" "$file"
        sed -i "s/{{expert_name}}/$EXPERT_NAME_SNAKE/g" "$file"
        sed -i "s/{{EXPERT_NAME_UPPER}}/$EXPERT_NAME_UPPER/g" "$file"
        sed -i "s/{{DOMAIN_DESCRIPTION}}/$DOMAIN_DESCRIPTION/g" "$file"
        sed -i "s/{{PORT}}/$PORT/g" "$file"
    fi
}

# Replace placeholders in all relevant files
find "$EXPERT_DIR" -type f \( -name "*.md" -o -name "*.py" -o -name "*.yaml" -o -name "*.yml" \) | while read -r file; do
    replace_placeholders "$file"
done

echo ""
echo -e "${GREEN}Expert '$EXPERT_NAME' created successfully!${NC}"
echo ""
echo "Location: $EXPERT_DIR"
echo "Port: $PORT"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit SKILL.md with domain knowledge"
echo "   $EXPERT_DIR/SKILL.md"
echo ""
echo "2. Add core knowledge files"
echo "   $EXPERT_DIR/knowledge/core/"
echo ""
echo "3. Configure organization patterns"
echo "   $EXPERT_DIR/knowledge/org-patterns/"
echo ""
echo "4. Review and update config.yaml"
echo "   $EXPERT_DIR/mcp-server/config.yaml"
echo ""
echo "5. Test the expert"
echo "   ./scripts/test-expert.sh $EXPERT_NAME"
echo ""
echo "6. Start the expert"
echo "   ./scripts/start-expert.sh $EXPERT_NAME"
echo ""
echo "7. Register in project/CLAUDE.md"
echo "   See: saddle/templates/expert-claude-snippet.md"
