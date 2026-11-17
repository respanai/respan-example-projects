# LiveKit voice demo (TypeScript)

The Python demo's call (`python/tracing/livekit-voice-demo`), on LiveKit Agents for
Node, traced by the published Respan SDK (`@respan/respan` +
`@respan/instrumentation-livekit` from npm). It runs the same end-to-end checks.

## Run it

```bash
cp .env.example .env    # then set RESPAN_API_KEY (and RESPAN_BASE_URL for staging)
./run.sh                # npm install on first run; starts the speech server; call + checks
```

Needs Node 20+, macOS and Python 3.11-3.13.

## What runs

- **The agent:** LiveKit's stock OpenAI STT / LLM / TTS plugins in an `AgentSession`
  with Silero VAD.
- **The LLM:** gpt-4o-mini through the Respan gateway.
- **Speech:** the Python demo's `speech_server.py`, a local OpenAI-compatible
  server (Whisper and macOS voices). `run.sh` starts and stops it.

`out/` holds the same files as the Python demo, except `call.wav`:
`otlp_payload.json`, `spans.json`, `session_turns.json` and `call.json`.
