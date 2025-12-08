#!/bin/bash

# Coverage script for envseal project
# This script runs tests with coverage reporting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running tests with coverage...${NC}"

# Run pytest with coverage
python -m pytest tests/ \
    --cov=src/envseal \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=xml \
    -v

# Check if coverage was generated
if [ -d "htmlcov" ]; then
    echo -e "${GREEN}Coverage report generated successfully!${NC}"
    echo -e "${YELLOW}HTML report location: htmlcov/index.html${NC}"
else
    echo -e "${RED}Coverage report generation failed!${NC}"
    exit 1
fi
