#!/bin/bash

# Detect GPU
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker"
source "$SCRIPT_DIR/detect_gpu.sh"
COMPOSE_FILE=$(get_compose_file)

# Stop and clean up containers and orphan networks
docker compose $COMPOSE_FILE down edu-chatbot-node --remove-orphans
docker compose $COMPOSE_FILE down --remove-orphans