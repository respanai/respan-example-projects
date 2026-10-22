# Ollama tracing examples

These scripts run the released official Ollama client against controlled HTTPX responses and native NDJSON streams. They run locally without credentials, a model download, or a running provider server. The SDK performs its own request serialization, typed response validation, and stream resource handling.

```bash
pip install -r requirements.txt
python run_all.py
```

For the source checkout under audit, install its package or settled wheel instead of the published instrumentation. Minimum-compatible released companions are `respan-tracing==2.17.0`, `respan-sdk==2.6.26`, `ollama==0.6.0`, AI semantic conventions 0.5.1, and OpenTelemetry 1.38.0 with instrumentation/semantic conventions 0.59b0. Current validation uses Ollama 0.6.3 and the latest released companions.

| Script | Native behavior |
|---|---|
| `01_chat.py` | 75-message history, native image encoding, structured JSON format, thinking and zero-valued options |
| `02_stream_generate.py` | 10,000-character text/reasoning stream, source cache/usage, partial close and unread close |
| `03_tool_calling.py` | SDK-generated callable schema, current tool calls, historical tool result and streamed tool call |
| `04_embeddings.py` | Modern batched and legacy 5001-dimensional vectors, empty inputs and zero counts |
| `05_expected_error.py` | Native HTTP 429, HTTP 200 event failure with partial output, empty generation text |
| `06_async.py` | Concurrent native async calls, async stream, pre-first aclose and embedding |
| `07_content_policy.py` | Restored late content veto and initial content veto, with native results retained |
| `08_optional_live.py` | Explicit optional inference against a real local Ollama server |

## Export controlled examples

Export is independently opt-in. Only export mode loads the repo's `.env`; invocation variables take precedence. Set `RESPAN_API_KEY` there or in the process environment.

```bash
RESPAN_EXAMPLE_EXPORT=1 \
RESPAN_EXAMPLE_RUN_ID=ollama-your-exact-run-marker \
python run_all.py
```

`RESPAN_EXAMPLE_ENV_FILE` selects another dotenv file. `RESPAN_TRACE_ENDPOINT` defaults to `https://api.respan.ai/api/v2/traces`. Local mode uses an in-memory exporter and prints local span counts. Audit-only `RESPAN_EXAMPLE_LOCAL_PATH` and `RESPAN_EXAMPLE_WIRE_PATH` optionally save local records and the exporter's actual HTTP bodies/status, respectively. Credentials and HTTP authorization headers are never saved by these observers.

## Optional real inference

Install a model on your Ollama server first, then explicitly enable the live script. An ambient `OLLAMA_HOST` alone does not turn fixture scripts into provider calls. Live inference and trace export are independent choices.

```bash
RESPAN_OLLAMA_LIVE=1 OLLAMA_MODEL=llama3.2 \
python 08_optional_live.py
```

Use `OLLAMA_HOST` if your server uses another address. This script makes an actual model call and may consume your server's resources; the default suite reports an explicit skip.

## Trace contract and bounds

Full sanitized native requests/responses remain in canonical `traceloop.entity.input`/`output`, including reasoning, schema/settings, complete histories and vectors. Embedding output remains complete vector(s), with its native nonvector envelope retained in capture-gated `respan.metadata.ollama.result`. Model, cache/usage, and HTTP status are source values; absent totals/status are omitted. Historical and current tool calls stay separate. Content vetoes remove captured bodies, tools, metadata and diagnostics while retaining native outcomes. No source payload truncation is introduced by the adapter; the OpenTelemetry SDK's attribute-count limit can bound indexed prompt/completion convenience fields, with full canonical data written last.

Streams are protocol proxies over the SDK's public Iterator/AsyncIterator contract; concrete generator identity changes. Native chunk identity, send/throw/asend/athrow, delegated generator attributes, close/aclose, errors and resources are preserved. Consume or close streams explicitly. Ollama 0.6.0 has no client close convenience method, so examples close its native underlying HTTPX client. SDK-native typed-field filtering and version-specific parameter support still apply.

Local success and accepted export HTTP responses are separate from stored-trace acceptance. Compare the exact run marker or actual exported trace IDs with complete same-run trees and details. Stored projection limitations must be reported separately from the source instrumentation contract.
