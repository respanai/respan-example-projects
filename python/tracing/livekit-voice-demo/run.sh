#!/usr/bin/env bash
# One command: set up (first run only), run the scripted voice call, check it end to end.
#   ./run.sh               new call + checks
#   ./run.sh <session id>  checks only, for an earlier call
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "Create .env with RESPAN_API_KEY=... (and RESPAN_BASE_URL=... for staging); see README.md" >&2
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  PY="${PYTHON:-python3}"
  "$PY" -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt
fi
exec .venv/bin/python e2e.py "$@"
