#!/bin/bash
# ==============================================================
# Vaani — Start All Containers
# ==============================================================
# Usage: ./start_all.sh <ENV> <IMAGE_TAG> <SERVICE_NAME>
#
# Examples:
#   ./start_all.sh dev latest              → Start all services
#   ./start_all.sh prod v1.0 backend       → Start only backend
# ==============================================================

ENV=$1
IMAGE_TAG=$2
SERVICE_NAME=$3

echo "=========================================="
echo " Starting Vaani containers"
echo " ENV:          ${ENV:-dev}"
echo " IMAGE_TAG:    ${IMAGE_TAG:-latest}"
echo " SERVICE_NAME: ${SERVICE_NAME:-all}"
echo "=========================================="

# Start specific service or all services
if [ -z "$SERVICE_NAME" ]; then
    docker-compose up -d --build
else
    docker-compose up -d --build $SERVICE_NAME
fi

echo "✅ Containers started!"
echo ""
echo " Frontend:  http://localhost:3000"
echo " Backend:   http://localhost:8000"
echo " API Docs:  http://localhost:8000/docs"
