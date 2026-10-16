# LiveKit Agents tracing examples

Eight controlled examples use the real LiveKit Agents LLMStream, function tools,
Session and OpenAI companion SDK. Model execution or HTTP transport is the fixture
boundary; no room, LiveKit cloud account or paid provider call is required by
default. Normal runs collect spans locally and do not load credentials or export.

```bash
python3 -m venv .venv-livekit
. .venv-livekit/bin/activate
pip install -r python/tracing/livekit/requirements.txt build poetry-core
# Until the companion SDK change is published, install only its target adapter.
pip install --no-deps --no-build-isolation -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-livekit
python python/tracing/livekit/run_all.py
```

The runner executes every script in an independent process with one exact marker,
a 60-second limit per script and an aggregate nonzero exit on any failure. Set
`LIVEKIT_RUNNER_REPORT` for its JSON result and `LIVEKIT_CAPTURE_DIR` for complete
local span records. Controlled validation covers LiveKit Agents and OpenAI plugin
1.6.0 and 1.8.4. Use the companion's compatible OpenAI SDK dependency; current
plugin 1.8.4 requires OpenAI<3. No editable Respan core packages are needed.

- `01_llm_chat.py`: actual native collect result, chat attributes and usage.
- `02_streaming_response.py`: full stream, early close and caller-context checks.
- `03_tool_calling.py`: current vs historical calls, full schemas, JSON argument
  strings, complete 5000-dimensional dense and 256-entry sparse tool values, IDs
  and native utility execution.
- `04_context_and_error.py`: returned unknown-tool failure and actual SDK 429.
- `05_live_openai.py`: native OpenAI companion with controlled HTTP/SSE by default.
- `06_content_privacy.py`: initial opt-out and a completed-parent veto before a
  delayed stream completes, plus a private parent created before activation.
  Unobserved local recording parent bounds conservatively deny child content;
  native results and actual usage are retained.
- `07_raw_usage.py`: absent and boolean provider usage before DTO coercion.
- `08_native_session.py`: room-free Session success/failure tool spans, preserving
  existing spans and native string outputs.

To export controlled traces, explicitly set `RESPAN_EXPORT=1` and
`RESPAN_EXAMPLE_RUN_ID` to your exact run marker. Only export/live modes load the
repository-root `.env`, with `override=False`; `RESPAN_ENV_FILE` selects another
file. Export uses `RESPAN_API_KEY` and optional `RESPAN_BASE_URL` (default
`https://api.respan.ai/api`). Local run markers are generated if not supplied.

```bash
RESPAN_EXPORT=1 RESPAN_EXAMPLE_RUN_ID=livekit-controlled-run \
  python python/tracing/livekit/run_all.py
```

For an optional paid OpenAI call, run only example 05 with
`RESPAN_LIVEKIT_LIVE=1`, `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, and
`RESPAN_LIVEKIT_MODEL`. This live path is credential gated and is not part of the
controlled fixture acceptance suite. It does not assume Respan Gateway access.

Private spans retain structural fields and actual usage, but omit source messages,
arguments, outputs and schemas. Credentials are redacted from captured content;
sensitive schema names retain structural types. Failed spans do not synthesize
usage/output/HTTP status. Session tool outputs follow the SDK's string rendering,
whereas utility tool results retain structured values. These examples do not
validate live voice rooms, audio/video, realtime models or every provider plugin.
Stored trace acceptance must compare the same run's exported body with its tree
and span details; HTTP 200 alone is not semantic acceptance.
