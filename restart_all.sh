#!/bin/bash
# ==============================================================
# Vaani — Restart All Containers
# ==============================================================
# Usage: ./restart_all.sh <ENV> <IMAGE_TAG> <SERVICE_NAME>
#
# Examples:
#   ./restart_all.sh dev latest              → Restart all services
#   ./restart_all.sh prod v1.0 backend       → Restart only backend
# ==============================================================

ENV=$1
IMAGE_TAG=$2
SERVICE_NAME=$3

echo "=========================================="
echo " Restarting Vaani containers"
echo " ENV:          ${ENV:-dev}"
echo " IMAGE_TAG:    ${IMAGE_TAG:-latest}"
echo " SERVICE_NAME: ${SERVICE_NAME:-all}"
echo "=========================================="

# Stop first, then start
./stop_all.sh $ENV $IMAGE_TAG $SERVICE_NAME
./start_all.sh $ENV $IMAGE_TAG $SERVICE_NAME

echo "✅ Containers restarted!"
