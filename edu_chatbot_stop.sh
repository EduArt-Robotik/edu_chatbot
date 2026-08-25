#!/bin/bash

# Detect GPU
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker"
source "$SCRIPT_DIR/detect_gpu.sh"
COMPOSE_FILE=$(get_compose_file)

if [[ "$1" == "--all" || "$1" == "all" ]]; then
    # Stop and clean up all containers from all profiles
    docker compose $COMPOSE_FILE --profile "*" down --remove-orphans
else
    # Stop and clean up the default service
    docker compose $COMPOSE_FILE down edu-chatbot-controller --remove-orphans
fi