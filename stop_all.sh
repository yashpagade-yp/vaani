#!/bin/bash
# ==============================================================
# Vaani — Stop All Containers
# ==============================================================
# Usage: ./stop_all.sh <ENV> <IMAGE_TAG> <SERVICE_NAME>
#
# Examples:
#   ./stop_all.sh dev latest              → Stop all services
#   ./stop_all.sh prod v1.0 backend       → Stop only backend
# ==============================================================

ENV=$1
IMAGE_TAG=$2
SERVICE_NAME=$3

echo "=========================================="
echo " Stopping Vaani containers"
echo " ENV:          ${ENV:-dev}"
echo " IMAGE_TAG:    ${IMAGE_TAG:-latest}"
echo " SERVICE_NAME: ${SERVICE_NAME:-all}"
echo "=========================================="

# Stop specific service or all services
if [ -z "$SERVICE_NAME" ]; then
    docker-compose down
else
    docker-compose stop $SERVICE_NAME
fi

echo "✅ Containers stopped!"
