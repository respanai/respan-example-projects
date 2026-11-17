# LiveKit voice demo (Python)

A real LiveKit voice agent, traced by the published Respan SDK
(`respan-ai` + `respan-instrumentation-livekit` from PyPI), with an end-to-end
check that reads the call back from the Respan API.

One scripted phone call to a dental clinic's receptionist agent. The caller asks
to move an appointment, then talks over the agent while it lists Thursday times,
and books Friday at 10.

## Run it

```bash
cp .env.example .env    # then set RESPAN_API_KEY (and RESPAN_BASE_URL for staging)
./run.sh                # first run builds .venv; then: the call + the checks
```

`./run.sh <session id>` re-checks an earlier call without making a new one.

Needs macOS (for its `say` voices) and Python 3.11-3.13. Only a Respan API key is
needed: the LLM (gpt-4o-mini) goes through the Respan gateway, and speech runs on
this machine.

## What runs

LiveKit Agents' real pipeline: `AgentSession` with Silero VAD, speech-to-text,
the LLM and text-to-speech, with interruptions on.

- **Speech-to-text:** Whisper (`faster-whisper`, `base.en`, CPU), as a LiveKit STT
  plugin (`local_speech.py`).
- **LLM:** gpt-4o-mini through the Respan gateway (`livekit-plugins-openai`).
- **Text-to-speech:** a macOS voice, as a LiveKit TTS plugin (`local_speech.py`).

The two ends of the phone line are stand-ins, because there is no LiveKit room.
The caller's microphone plays pre-recorded speech in real time. The agent's
speaker plays out on a real-time clock and stops when it is talked over, so the
interruption is the real one.

## What it writes (`out/`)

| File | What it is |
|---|---|
| `otlp_payload.json` | The exact JSON bodies the SDK POSTed to `/v2/traces`. |
| `spans.json` | The same spans, flattened: LiveKit name, trace, session, `voice.*` timings. |
| `session_turns.json` | The API's answer: `GET /api/sessions/<id>/?view=turns`. |
| `call.wav` | The whole call, both sides, as heard. |
| `call.json` | The session id, the transcript and the export counts. |

## What the checks prove

- **One session:** the call is one session, and every exported span carries its id.
- **One trace per turn:** each caller turn is its own trace. The only other trace
  is the call itself, whose id is the session id.
- **Voice timings:** every turn carries the user's wait, STT delay, LLM time to
  first token and TTS time to first audio, in ms.
- **Interruption:** the reply the caller talked over (turn 2) is flagged
  interrupted, and only that turn.
- **Call summary:** `voice_summary` counts 4 turns and 1 interruption, with p50/p95
  waits.

`speech_server.py` serves the same speech as an OpenAI-compatible API for the
TypeScript demo (`typescript/tracing/livekit-voice-demo`).
