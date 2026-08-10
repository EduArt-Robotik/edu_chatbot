#!/bin/bash
set -eu
grep -v '^\s*#' /models.txt | grep -v '^\s*$' | while read -r model; do
  echo "Pulling $model..."
  ollama pull "$model"
done