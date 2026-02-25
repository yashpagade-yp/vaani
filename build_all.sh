#!/bin/bash
# ==============================================================
# Vaani — Build All Containers
# ==============================================================
# Usage: ./build_all.sh <ENV> <IMAGE_TAG> <SERVICE_NAME>
#
# Examples:
#   ./build_all.sh dev latest              → Build all services
#   ./build_all.sh prod v1.0 backend       → Build only backend
# ==============================================================

ENV=$1
IMAGE_TAG=$2
SERVICE_NAME=$3

echo "=========================================="
echo " Building Vaani containers"
echo " ENV:          ${ENV:-dev}"
echo " IMAGE_TAG:    ${IMAGE_TAG:-latest}"
echo " SERVICE_NAME: ${SERVICE_NAME:-all}"
echo "=========================================="

# Build specific service or all services
if [ -z "$SERVICE_NAME" ]; then
    docker-compose build --no-cache
else
    docker-compose build --no-cache $SERVICE_NAME
fi

echo "✅ Build complete!"
