#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"

# Use local virtual environment if present
if [ -f "$DIR/.venv/bin/python" ]; then
    PY="$DIR/.venv/bin/python"
elif [ -f "$DIR/Hadi_ver/.venv/bin/python" ]; then
    PY="$DIR/Hadi_ver/.venv/bin/python"
else
    PY="python3"
fi

echo "=========================================================="
echo " Starting Arbiter — SOC Telemetry & Incident Workspace   "
echo " Database: PostgreSQL                                     "
echo " Access URL: http://${HOST}:${PORT}                       "
echo "=========================================================="

exec "$PY" -m uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
