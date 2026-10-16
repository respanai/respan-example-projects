# IBM watsonx.ai tracing examples

These scripts create the real installed IBM `APIClient`, `ModelInference`, and `Embeddings` with the public HTTPX client injection API. Native `httpx.MockTransport` supplies controlled JSON/SSE bytes, and the IBM SDK performs request serialization, response parsing, batching, native errors, and cleanup. No SDK methods are replaced and no uninitialized vendor objects are used. Local execution requires no provider or Respan credentials and records spans in memory.

```bash
python -m pip install -r requirements.txt
python run_all.py
```

Tested with IBM SDK 1.8.0/current released companions and IBM SDK 1.6.3/exact declared floors. This checkout's instrumentation version remains 0.1.0; the published package is 0.1.1.

| Script | Native scenario |
| --- | --- |
| `01_text_generation.py` | generation, convenience text, multiple native batch requests, source zero settings |
| `02_streaming.py` | 300 SSE frames, fragmented tool arguments, partial and unopened close |
| `03_chat_tool_calling.py` | 75-message history, historical/current tool IDs, schema, zero settings, reasoning, empty feedback |
| `04_async_model_calls.py` | all four async model methods and stream cleanup |
| `05_embeddings.py` | six sync/async embedding methods, batch requests, full 5001-element vectors |
| `06_expected_error.py` | native HTTP 429 and partial SSE error |
| `07_content_policy.py` | irreversible late stream and initial ancestor content veto |
| `08_optional_live.py` | independently enabled real provider request; skipped by default |

Each controlled script creates one workflow trace. Native convenience calls create one inference span. Optional export is explicit:

```bash
RESPAN_EXAMPLE_EXPORT=1 \
RESPAN_EXAMPLE_ENV_FILE=/absolute/path/to/.env \
RESPAN_EXAMPLE_RUN_ID=watsonx-controlled-run \
python run_all.py
```

The `.env` is read only for explicit Respan export. Configure `RESPAN_API_KEY`; `RESPAN_TRACE_ENDPOINT` defaults to `https://api.respan.ai/api/v2/traces`. `RESPAN_EXAMPLE_WIRE_PATH` records the actual exporter HTTP body/status, and `RESPAN_EXAMPLE_LOCAL_PATH` records same-run local spans. Use synthetic content for these artifacts. Export uses the released `RespanSpanExporter` directly.

A real IBM request is a separate opt-in. Set `RESPAN_WATSONX_LIVE=1`, `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, and an explicitly chosen `WATSONX_MODEL_ID` in the process environment, then run `08_optional_live.py`. `WATSONX_URL` defaults to IBM's US South endpoint. This mode can incur provider charges and uses normal native authentication and scope validation; it is skipped by the controlled suite. Export does not enable provider access.

Canonical source I/O retains full sanitized payloads and full vectors. Native generator identity changes to a protocol proxy; native operations and resources are delegated. Async streams must be explicitly closed. Native worker-thread batching can omit unobserved HTTP status/aggregate usage. Default OpenTelemetry 128-attribute limits can bound indexed convenience fields while canonical full I/O remains preserved. Backend stored projections are assessed separately from local/export success.
