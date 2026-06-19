#!/usr/bin/env bash
# Run VisionGuard locally WITHOUT Docker (simplest demo path).
# Backend on :8000 (SQLite + inline processing), frontend on :5173.
#
# Usage:  bash scripts/run_local.sh
# Stop:   Ctrl-C (kills both)
set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

# --- backend ---
if [ ! -d .venv ]; then
  python3.11 -m venv .venv
  ./.venv/bin/pip install -q -r backend/requirements.txt -r ml/requirements.txt
fi

export DATABASE_URL="sqlite:///./data/visionguard.db"
export PROCESS_MODE="inline"
echo "Starting API on http://localhost:8000 (docs at /docs) ..."
( cd backend && "$ROOT/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 ) &
API_PID=$!

# --- frontend ---
export PATH="/opt/homebrew/bin:$PATH"
if [ ! -d frontend/node_modules ]; then
  ( cd frontend && npm install )
fi
echo "Starting frontend on http://localhost:5173 ..."
( cd frontend && npm run dev ) &
FE_PID=$!

trap "echo stopping; kill $API_PID $FE_PID 2>/dev/null" INT TERM
wait
