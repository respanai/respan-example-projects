# Writer tracing examples

The examples use released Writer clients and typed responses with controlled HTTPX transport JSON/SSE frames. They record locally by default and require no Writer credential or production inference call.

## Install and run

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
RESPAN_EXAMPLE_RUN_ID=my-exact-marker .venv/bin/python run_all.py
```

For local development, install the Writer target after the released dependencies:

```bash
.venv/bin/pip install --no-deps --no-build-isolation -e   ../../../../respan/python-sdks/instrumentations/respan-instrumentation-writer
```

The native `writer-sdk` floor is 2.3.0; `writerai` is only the alias distribution. Current and minimum profiles exercise SDK 3.0.0 and 2.3.0. Released facade 4.1.0 is pinned to allow the checkout package version with released companions without editing release versions.

`run_all.py` runs fourteen numbered scripts with one exact run marker and returns nonzero for failures. Thirteen controlled scripts cover:

- Chat and text generation, native structured parsing and connected tool execution.
- All synchronous/asynchronous resource methods: graphs, application generation, vision, translation, web search and PDF parsing.
- Four native streaming resource families, 300 chunks, early/unread close and original context-manager behavior.
- Complete 75-message histories, schemas, native extra 5,001-value vectors, empty provider feedback and initial/late privacy denial.
- Native retries, response callbacks, HTTP 429 and partial SSE `event: error` behavior.

The fourteenth script explicitly skips live access unless enabled. Native PDF parsing is deprecated in SDK 3.0.0; its current callable API and warning remain unchanged. There is no invented embedding API: the vector scenario preserves actual extra native response data in the full JSON payload.

Public Writer stream identity and type are preserved through owned private iterator/close taps. The SDK consumes generators, builds structured schemas, parses models and owns HTTP cleanup. The adapter adds no implicit payload truncation; native OpenTelemetry bounds may limit indexed projections, while full canonical payloads are written last.

## Export and live opt-ins

Export controlled traces with a configured `RESPAN_API_KEY` in the repository `.env` or environment:

```bash
RESPAN_EXAMPLE_EXPORT=1 RESPAN_EXAMPLE_RUN_ID=my-export-marker   .venv/bin/python run_all.py
```

`.env` is loaded only for explicit export or live calls. Set `RESPAN_EXAMPLE_REPORT_DIR` to save local OTLP span bodies. Run metadata uses the exact caller marker; denied child spans intentionally retain no content metadata.

Live Writer calls are separate and can incur provider charges:

```bash
WRITER_EXAMPLE_LIVE=1 WRITER_API_KEY=... WRITER_MODEL=your-model   .venv/bin/python 14_live_provider.py
```

Legacy `WRITER_EXAMPLE_MODE=live` also enables live access in the original numbered scenarios and requires the corresponding provider model, graph, application and file configuration. Local compatibility, real exporter HTTP success and scoped stored-trace semantics are reported separately.
