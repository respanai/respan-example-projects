# Python Anthropic tracing

These examples run the released Anthropic SDK against controlled HTTP and SSE
responses. They record spans locally by default and require no provider keys.
The suite covers stable/beta messages, raw and helper streams, partial close,
async calls, tool history and complete arguments, thinking blocks, native typed
parse/stream helpers, provider errors, capture vetoes, suppression, and available
managed-session event streams. Optional APIs absent in an older SDK are reported
as skipped. Managed-session fixtures never create or deploy agent resources.

Install the package under review into an isolated environment, then run:

```bash
python -m pip install -r python/tracing/anthropic/requirements.txt
RESPAN_EXAMPLE_RUN_ID=my-marker python python/tracing/anthropic/run_all.py
```

Use `RESPAN_EXAMPLE_OUTPUT_DIR=/path/to/evidence` to save local span evidence.
The examples import installed distributions and do not add sibling source trees
to Python's import path.

To export the same controlled suite explicitly:

```bash
RESPAN_EXAMPLE_EXPORT=1 RESPAN_EXAMPLE_ENV_FILE=/path/to/.env \
RESPAN_EXAMPLE_RUN_ID=my-export-marker RESPAN_EXAMPLE_OUTPUT_DIR=/path/to/evidence \
python python/tracing/anthropic/run_all.py
```

Only export mode loads `.env`. It uses the released `RespanSpanExporter` against
`https://api.respan.ai/api/v2/traces`, requires `RESPAN_API_KEY`, and records the
actual HTTP bodies observed at the exporter's POST boundary. HTTP acceptance
and local assertions are separate from stored-trace semantic verification.

`09_live_provider.py` is skipped by default. A paid native provider call requires
explicit `RESPAN_EXAMPLE_LIVE=1`, `ANTHROPIC_API_KEY`, and `ANTHROPIC_MODEL` in the
process environment. Managed-agent deployment and paid remote tool execution
remain external provider paths; the controlled fixtures do not validate them.
