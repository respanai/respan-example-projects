# Aleph Alpha native tracing examples

These scripts use released `aleph-alpha-client` request/response types and its actual HTTP/SSE transport. They default to an isolated local server, local OpenTelemetry recording, and no provider credentials or export.

```bash
python -m pip install respan-instrumentation-aleph-alpha aleph-alpha-client python-dotenv
python python/tracing/aleph-alpha/01_chat.py
```

For a checkout under audit, install the target package editable or use its built wheel with compatible released companion packages. Scripts never insert local source directories into `sys.path`.

| Script | Native coverage |
| --- | --- |
| `01_chat.py` | 75-message history, native tool IDs/arguments, tool schema and redacted sensitive defaults/examples |
| `02_completion.py` | Full native completion response and successful empty candidate list |
| `03_embeddings.py` | Classic, OpenAI-shaped, semantic, batch and instructable embeddings with 5,001-value vectors |
| `04_async_streaming.py` | Actual completion/chat SSE parser items, usage and quoted credentials split across native output chunks |
| `05_evaluate_explain.py` | Native evaluation and explanation envelopes |
| `06_privacy.py` | Initial opt-out, native error diagnostics, pre-detach veto and a finished parent veto |
| `07_lifecycle.py` | Close before pull, partial close, two pending siblings and abandonment without consumption |
| `08_async_apis.py` | All eight supported eager async APIs, including native batch embedding aggregation |

Each script records a workflow and connected native call spans. Optional evidence files contain local spans and the exporter's actual HTTP bodies, using `RESPAN_EXAMPLE_OUTPUT_DIR`. `RESPAN_EXAMPLE_RUN_ID` sets the exact run marker. All fixture content is synthetic. Local/parser checks and HTTP export acceptance are separate from backend projection checks.

Controlled export requires explicit opt-in:

```bash
RESPAN_EXAMPLE_EXPORT=1 \
RESPAN_EXAMPLE_ENV_FILE=/absolute/path/to/.env \
RESPAN_EXAMPLE_RUN_ID=your-unique-run-id \
RESPAN_EXAMPLE_OUTPUT_DIR=/absolute/path/to/evidence \
python python/tracing/aleph-alpha/03_embeddings.py
```

Only this export opt-in loads `.env` (without overriding existing values). It uses the released `RespanSpanExporter` at `https://api.respan.ai/api/v2/traces`. The scripts require `RESPAN_API_KEY` or `RESPAN_GATEWAY_API_KEY` for export; they do not print credentials. Default local execution does not read `.env`.

Real provider requests are a separate optional path. Set `ALEPH_ALPHA_EXAMPLE_REAL=1`, `ALEPH_ALPHA_API_KEY`, `ALEPH_ALPHA_HOST`, and `ALEPH_ALPHA_MODEL` explicitly for the basic native API examples. Your provider account must support those model/API combinations, and requests may incur charges. Privacy/error/lifecycle fault scenarios require controlled mode. The archived SDK has no managed agent/deployment surface in this package, and translation, reranking, tokenization, steering-concept creation, downloads and administrative endpoints remain outside the declared instrumentation scope.

The async stream wrapper implements the declared `AsyncGenerator` protocol and preserves returned native items; its concrete type differs. Explicitly close partially consumed streams and clients. Abandonment ends telemetry without starting or draining the native generator. Full canonical content survives indexed OTel attribute bounds. Native usage fields are retained without invented totals or success HTTP codes; API errors retain their original SDK exception. Credential text is redacted in telemetry while caller-owned responses remain unchanged.
