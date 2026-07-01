#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

trap 'kill $(jobs -p) 2>/dev/null' EXIT

(cd "$ROOT/backend" && .venv/bin/python main.py) &
(cd "$ROOT/frontend" && npm run dev) &

wait
