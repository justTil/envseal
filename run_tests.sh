#!/bin/bash

# Test runner script for envseal project
# This script runs pytest with verbose output

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running tests...${NC}"

# Run pytest with verbose output
python -m pytest tests/ -v

echo -e "${GREEN}Tests completed successfully!${NC}"
