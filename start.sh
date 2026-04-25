#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "Starting Flight Planner API..."
uv run flight-api &
API_PID=$!

echo "Starting Angular frontend..."
cd "$ROOT/frontend" && npm start &
FRONTEND_PID=$!

echo ""
echo "Services running:"
echo "  API      -> http://localhost:8000  (PID $API_PID)"
echo "  Frontend -> http://localhost:4200  (PID $FRONTEND_PID)"
echo ""
echo "Press Ctrl+C to stop both."

stop() {
  echo ""
  echo "Stopping services..."
  kill "$API_PID" "$FRONTEND_PID" 2>/dev/null || true
  exit 0
}

trap stop INT TERM
wait
