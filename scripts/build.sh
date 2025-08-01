#!/bin/bash
set -e

# Build script for ClaudeLens Docker image

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get version from package.json or use git commit
VERSION=${VERSION:-$(git describe --tags --always --dirty)}

echo -e "${GREEN}Building ClaudeLens Docker image v${VERSION}${NC}"

# Build the image
docker build \
    -f docker/Dockerfile \
    -t claudelens:${VERSION} \
    -t claudelens:latest \
    --build-arg VERSION=${VERSION} \
    .

echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${YELLOW}Tagged as:${NC}"
echo "  - claudelens:${VERSION}"
echo "  - claudelens:latest"

# Optionally run tests on the built image
if [ "$1" == "--test" ]; then
    echo -e "${YELLOW}Running container tests...${NC}"
    docker run --rm claudelens:${VERSION} python -m pytest /app/backend/tests/test_health.py
fi

# Show image size
echo -e "${YELLOW}Image size:${NC}"
docker images claudelens:${VERSION} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"