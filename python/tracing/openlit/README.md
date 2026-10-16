# OpenLIT tracing examples

The nine scripts use released OpenLIT and OpenAI APIs with controlled HTTP fixtures. By default they collect spans locally and require no model or Respan credential. They exercise sync/async Chat Completions and Responses, native streaming and early close, actual tool execution, 5000-element embeddings and tool vectors, a controlled 429 error, typed Responses.parse, content opt-outs and delayed-parent privacy, and invalid raw usage counts.

Install from this examples repository:

```bash
python -m venv /private/tmp/openlit-examples
/private/tmp/openlit-examples/bin/pip install -r python/tracing/openlit/requirements.txt
/private/tmp/openlit-examples/bin/python python/tracing/openlit/run_all_examples.py
```

For a local adapter checkout, install only that package with `pip install -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-openlit`; keep the Respan core packages released.

The runner starts a fresh process per script, applies a 60-second timeout, continues after failures, and shares one exact `RESPAN_EXAMPLE_RUN_ID` (generated locally if omitted). Set `OPENLIT_CAPTURE_DIR` to save local span JSON. OpenLIT 1.45.0 with OpenAI 2.54.0 and OpenLIT 1.44.0 with OpenAI 1.92.0 are tested; OpenLIT declares OpenAI <3. Native Responses.parse instrumentation is gated to OpenLIT 1.45, so script 06 explicitly skips at 1.44.

Trace export is a separate opt-in:

```bash
RESPAN_EXPORT=1 RESPAN_ENV_FILE=/path/to/.env \
  RESPAN_EXAMPLE_RUN_ID=openlit-controlled-unique-marker \
  /private/tmp/openlit-examples/bin/python python/tracing/openlit/run_all_examples.py
```

The env file needs `RESPAN_API_KEY`; shell variables take precedence because dotenv uses `override=False`. Export goes to the configured `RESPAN_BASE_URL` (default `https://api.respan.ai/api`). The exact marker is attached to every span for scoped stored-trace inspection. An accepted HTTP request alone does not prove stored payload or status fidelity.

`RESPAN_OPENLIT_LIVE=1` lets the first three scenarios use `OPENAI_API_KEY` and optional `OPENAI_BASE_URL`. The remaining scenarios retain controlled fixtures. Live models, credentials, billing and provider-specific tool/stream behavior are not validated by the fixture run. The helper workflow/tool contexts use native `openlit.start_trace`; they describe the actual application call and preserve the returned value.
