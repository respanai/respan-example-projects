#!/usr/bin/env bash
# One command: set up (first run only), start the local speech server, run the
# scripted voice call, check it end to end.
#   ./run.sh               new call + checks
#   ./run.sh <session id>  checks only, for an earlier call
set -euo pipefail
cd "$(dirname "$0")"
PY_DEMO="../../../python/tracing/livekit-voice-demo"
PORT="${SPEECH_PORT:-8765}"
export SPEECH_BASE_URL="http://127.0.0.1:${PORT}/v1"

if [ ! -f .env ]; then
  echo "Create .env with RESPAN_API_KEY=... (and RESPAN_BASE_URL=... for staging); see README.md" >&2
  exit 1
fi
[ -d node_modules ] || npm install --no-audit --no-fund

# Speech (Whisper + macOS voices) runs in the Python demo's venv.
if [ ! -x "$PY_DEMO/.venv/bin/python" ]; then
  (cd "$PY_DEMO" && "${PYTHON:-python3}" -m venv .venv && .venv/bin/pip install -q --upgrade pip \
    && .venv/bin/pip install -q -r requirements.txt)
fi
if ! curl -s -o /dev/null "http://127.0.0.1:${PORT}/"; then
  (cd "$PY_DEMO" && .venv/bin/python speech_server.py "$PORT" > /tmp/respan_speech_server.log 2>&1) &
  SPEECH_PID=$!
  trap 'kill $SPEECH_PID 2>/dev/null || true' EXIT
  for _ in $(seq 1 60); do
    grep -q "speech server on" /tmp/respan_speech_server.log 2>/dev/null && break
    sleep 1
  done
fi

# The SDK prints its own debug lines; keep the demo's output readable.
npx tsx e2e.ts "$@" 2>&1 | grep -vE '^\[Respan|^\s*$|^Respan tracing initialized'
exit "${PIPESTATUS[0]}"
