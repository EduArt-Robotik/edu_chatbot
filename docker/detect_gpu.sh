#!/bin/bash

# Function to return the appropriate docker compose flags for the detected GPU
get_compose_file() {
  if lspci | grep -i "VGA\|3D\|Display" | grep -iq "NVIDIA"; then
    echo "NVIDIA GPU detected. Using NVIDIA docker-compose configuration." >&2
    echo "-f docker-compose.yaml -f docker/docker-compose.nvidia.yaml"
  elif lspci | grep -i "VGA\|3D\|Display" | grep -iqE "AMD|ATI"; then
    echo "AMD GPU detected. Using AMD docker-compose configuration." >&2
    echo "-f docker-compose.yaml -f docker/docker-compose.amd.yaml"
  else
    echo "No GPU detected. Using CPU fallback." >&2
    echo ""
  fi
}