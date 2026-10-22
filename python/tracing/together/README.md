# Together tracing examples

These examples invoke the official Together v2 clients against controlled HTTPX responses by default. The native SDK parses the JSON and SSE bytes into its real response models and streams. Traces stay in a local in-memory exporter unless export is explicitly enabled.

## Install and run

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
RESPAN_EXAMPLE_RUN_ID=my-exact-marker .venv/bin/python run_all.py
```

For development, install this target package from the SDK checkout after the released dependencies:

```bash
.venv/bin/pip install --no-build-isolation --no-deps -e   ../../../../respan/python-sdks/instrumentations/respan-instrumentation-together
```

The released facade `respan-ai==4.1.0` is pinned to allow testing the checkout package version with released companions. This does not change the package release version. Current and exact minimum profiles use Together `2.39.0` and `2.0.0` respectively.

`run_all.py` runs all thirteen numbered scripts with one exact marker, a per-script timeout and a nonzero result if any script fails. Twelve scripts run controlled scenarios; the final live-provider example reports an explicit skip unless enabled.

| Script | Native scenario |
|---|---|
| 01 | Chat completion |
| 02 | Seventy streaming chat chunks |
| 03 | Async chat completion |
| 04 | Text completion |
| 05 | Full 5,001-dimensional embedding vectors |
| 06 | Reranking |
| 07 | Image generation with base64 payload |
| 08 | Connected model/tool execution and tool result |
| 09 | Expected native provider HTTP 429 |
| 10 | All async operations, streaming and unread close |
| 11 | Empty native feedback, initial denial and irreversible late denial |
| 12 | Native retry/callbacks, stream context manager and close |
| 13 | Optional live Together chat |

Public Together stream identity and concrete type are preserved. The adapter observes the native private iterator and close method as the caller consumes or closes it; it does not eagerly drain the body. Embeddings retain all vectors in canonical output and the remaining source response envelope in owned capture-gated metadata. OpenTelemetry's attribute-count bound can limit indexed projections; full canonical payloads are retained.

## Optional export and live calls

To export controlled traces to Respan, provide `RESPAN_API_KEY` in the repository `.env` or environment:

```bash
RESPAN_EXAMPLE_EXPORT=1 RESPAN_EXAMPLE_RUN_ID=my-export-marker   .venv/bin/python run_all.py
```

The `.env` is loaded only for explicit export or live calls. Set `RESPAN_EXAMPLE_REPORT_DIR` to save the local OTLP span bodies. The exact run marker is recorded as `run_id` and `example_run_id` metadata on content-eligible spans.

Live provider access is a separate opt-in and can incur provider charges:

```bash
RESPAN_TOGETHER_LIVE=1 TOGETHER_API_KEY=...   RESPAN_TOGETHER_MODEL=your-model .venv/bin/python 13_live_provider.py
```

The model must be supplied explicitly. The other controlled fixtures require no Together credential or production service call. Local success, successful Respan HTTP export and stored-trace semantic acceptance are separate checks.
