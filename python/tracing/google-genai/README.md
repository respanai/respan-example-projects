# Google GenAI tracing examples

These examples trace the official `google-genai` Python SDK with Respan. They load environment variables from the repository root `.env` file.

Required for exporting traces:

```bash
RESPAN_API_KEY=...
```

For Gemini calls, use one of these options:

```bash
# Direct Google API calls, still traced to Respan
GOOGLE_API_KEY=...
# or
GEMINI_API_KEY=...
```

If neither Google key is set, the examples route through the Respan Gemini gateway with `RESPAN_API_KEY`. That requires Gemini provider credentials or managed credits configured on the Respan account.

Optional environment variables:

```bash
RESPAN_BASE_URL=https://api.respan.ai/api
RESPAN_GOOGLE_GENAI_MODEL=gemini-2.5-flash
```

Run one script at a time:

```bash
python 01_generate_content.py
python 02_stream_content.py
python 03_async_generate_content.py
python 04_tool_calling.py
```

Each script prints both a `custom_identifier` and `workflow_name`. The workflow name is also used as the Respan trace group identifier so the run is easy to find in traces and MCP lookups.

## Current SDK compatibility suite

Install `requirements.txt` and the paired local instrumentation update, then run:

```bash
RESPAN_EXAMPLE_RUN_ID=your-google-marker python run_all.py --mode fixture
```

The default fixture mode runs the released Google SDK 2.28 HTTP request and
response handling against deterministic transports. It makes no model-provider
requests, but exports the resulting traces to the configured Respan destination.
The seven scenarios produce nineteen spans:

| Script | Coverage |
| --- | --- |
| `01_generate_content.py` | Sync generation and reported usage |
| `02_stream_content.py` | Sync streaming |
| `03_async_generate_content.py` | Async generation |
| `04_tool_calling.py` | Model function call, tool execution, and follow-up |
| `05_embed_content.py` | Sync and async vectors, multimodal input, Vertex token statistics |
| `06_async_stream_content.py` | Async streaming |
| `07_embedding_error.py` | Controlled provider-shaped error with exception passthrough |

Use `--mode live` for the first six scenarios against configured Google or
Gateway credentials. Set `RESPAN_GOOGLE_EMBEDDING_MODEL` to override the embedding
model (default `gemini-embedding-001`). Live mode omits the fixture-only
multimodal/Vertex subcases and the controlled error scenario. Direct script
execution retains live mode unless `RESPAN_GOOGLE_GENAI_MODE=fixture` is set.

For semantic acceptance, filter Respan MCP logs by exact `metadata__run_id`
matching the printed marker, then inspect trees and full log details. Verify
parent links, tool payloads, models, actual reported usage, full embedding
vectors, and the controlled error. A completed local runner is not stored-trace
acceptance.
