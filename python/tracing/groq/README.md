# Groq tracing examples

Nine scripts exercise the official Groq Python SDK 1.7.0 with Respan:

| Script | Coverage |
|---|---|
| `01_chat_completion.py` | Sync chat |
| `02_streaming.py` | Streamed text and trailing usage |
| `03_tool_calling.py` | Tool-only response, tool execution and follow-up history |
| `04_async_streams.py` | Async chat, fragmented tool-call stream and early close |
| `05_response_helpers.py` | Native raw response and lazy HTTP response helpers |
| `06_controlled_error.py` | Controlled 503 preserving the SDK exception |
| `07_structured_multimodal.py` | JSON schema/reasoning controls and image/text input |
| `08_embeddings.py` | Float and base64 vectors, sync and async |
| `09_audio.py` | Transcription, translation, speech and async lazy audio reads |

## Setup

Use Python 3.11–3.13. Until the companion adapter update is released, install
requirements and the local adapter checkout in **one resolver operation**:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -e /absolute/path/to/respan/python-sdks/instrumentations/respan-instrumentation-groq
```

Core Respan dependencies resolve from released packages; no editable core
checkout is required. After the adapter release, plain `pip install -r
requirements.txt` can replace the checkout installation.

Set `RESPAN_API_KEY` in the repository root `.env` or in the environment.
`RESPAN_BASE_URL` defaults to `https://api.respan.ai/api`. Existing environment
variables take precedence over `.env`.

## Complete synthetic suite

```bash
RESPAN_GROQ_FIXTURE=1 RESPAN_EXAMPLE_RUN_ID=groq-my-audit python run_all.py
```

The fixture uses the real Groq SDK with an `httpx.MockTransport`; it makes no
model-provider request and needs no `GROQ_API_KEY`. It exports synthetic prompts,
responses, tool arguments, vectors, audio metadata/base64 bytes and controlled
errors to Respan. The runner uses one exact `metadata.run_id` across all scripts
and launches each in a separate process. Inspect that marker through Respan MCP
for actual stored trace acceptance.

For direct Groq calls, unset `RESPAN_GROQ_FIXTURE` and set `GROQ_API_KEY` and
`GROQ_MODEL`. The first three scripts also preserve the existing Respan gateway
fallback when no Groq key is present. Async and inference examples need direct
Groq credentials or fixture mode. The controlled-error and audio scripts require
fixture mode because their failures/audio bytes are intentionally synthetic.
The multimodal/JSON-schema example may need separate model choices for a live
provider; synthetic validation checks SDK transport and tracing semantics, not
model capability combinations.

Chat tool execution is decorated separately. An early-closed stream has partial
content and no usage unless the provider sent usage before close. Speech capture
is capped at 64 KiB with an explicit truncation flag; uploads are represented by
filename metadata without reading file contents. JSON response helpers record
output on `parse()`; unparsed closes do not fabricate a response.
