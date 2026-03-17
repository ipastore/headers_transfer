#!/usr/bin/env bash
# run.sh — Run extract.py inside Docker with local assets mounted.
#
# Usage:
#   ./run.sh                          # batch: all images in assets/screens/
#   ./run.sh --file 1.jpg             # single player
#   ./run.sh --dry-run --verbose      # inspect without writing
#   ./run.sh --reset                  # clear all rows below header
#   ./run.sh --fallback               # skip primary model
#   ./run.sh --file 1.jpg --dry-run   # combine flags freely

set -e

IMAGE="headers-transfer"
ASSETS_DIR="$(pwd)/assets"
ENV_FILE="$(pwd)/.env"

# Build image if it doesn't exist yet
if ! docker image inspect "$IMAGE" &>/dev/null; then
  echo "Image '$IMAGE' not found — building..."
  docker build -t "$IMAGE" .
fi

docker run --rm \
  -v "$ASSETS_DIR:/app/assets" \
  --env-file "$ENV_FILE" \
  "$IMAGE" \
  python extract.py assets/screens/ assets/ScoutDecisionPlayerImport.xlsx "$@"
