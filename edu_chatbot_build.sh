#!/bin/bash

# Detect GPU
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker"
source "$SCRIPT_DIR/detect_gpu.sh"
COMPOSE_FILE=$(get_compose_file)

# Build the base image first so downstream images can consume it
echo "Building base image (edu_ros_base)..."
docker compose $COMPOSE_FILE build edu_ros_base

# Build the remaining services
echo "Building all services..."
docker compose $COMPOSE_FILE --profile "*" build