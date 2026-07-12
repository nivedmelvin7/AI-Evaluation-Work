#!/usr/bin/env bash
# Run the Engineering Report Evaluation stack.
# Usage:
#   ./run.sh          — build frontend + start server (production mode)
#   ./run.sh --dev    — start server with hot-reload, skip frontend build
#   ./run.sh --build  — only build frontend, don't start server

set -e
cd "$(dirname "$0")"

MODE="prod"
BUILD_ONLY=false
for arg in "$@"; do
  case $arg in
    --dev)   MODE="dev" ;;
    --build) BUILD_ONLY=true ;;
  esac
done

# ── Frontend build ─────────────────────────────────────────────────────────────
if [ "$MODE" != "dev" ]; then
  echo "Building frontend..."
  cd frontend
  npm install --silent
  npm run build
  cd ..
  echo "Frontend built → frontend/dist/"
fi

[ "$BUILD_ONLY" = true ] && exit 0

# ── Backend ────────────────────────────────────────────────────────────────────
if [ "$MODE" = "dev" ]; then
  echo "Starting FastAPI in dev mode (hot-reload)..."
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
  echo "Starting FastAPI server..."
  python main.py
fi
