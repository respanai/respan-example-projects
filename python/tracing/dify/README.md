# Dify Python Tracing Examples

These examples exercise the first-party `respan-instrumentation-dify` package
with the real `dify-client` Python package.

The scripts load the repo-root `.env` in `respan-example-projects/.env`. If no
`DIFY_BASE_URL` is configured, they start a local Dify-compatible HTTP server so
the full tracing path is runnable with only `RESPAN_API_KEY`.

## Setup

From this directory:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt \
  -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-dify
```

## Run

```bash
DIFY_USE_FIXTURES=1 .venv/bin/python run_all.py
```

`run_all.py` generates and prints one `RESPAN_EXAMPLE_RUN_ID` and passes it to
all nine child scenarios. Set it explicitly when you want a predetermined
platform audit marker:

```bash
RESPAN_EXAMPLE_RUN_ID=dify-py-audit-001 DIFY_USE_FIXTURES=1 .venv/bin/python run_all.py
```

Primary examples:

- `01_chat_blocking.py` - blocking chat messages
- `02_chat_streaming.py` - streaming chat messages
- `03_completion.py` - text completion messages
- `04_workflow_and_api.py` - workflow run, parameters, conversations, messages, feedback, rename
- `05_respan_context_and_files.py` - file upload, multimodal file reference, propagated Respan attributes
- `06_async_chat_and_workflow.py` - refreshed-SDK async chat and workflow streaming (cleanly skips on released 0.1.10)
- `07_knowledge_workspace.py` - refreshed-SDK Knowledge Base, RAG pipeline, and Workspace operations (cleanly skips on released 0.1.10)

Compatibility aliases are kept for the previous filenames:
`hello_world.py`, `streaming.py`, `tracing.py`, `gateway.py`, and
`respan_params.py`.

## Real Dify Apps

Set `DIFY_BASE_URL` and one or more Dify app keys in `.env` to run against a
real Dify deployment. Without those variables, the local test server returns
Dify-shaped responses and the Respan instrumentation still exports live spans.

Additional scenarios cover early-close/error streams (`08_stream_lifecycle.py`)
and content opt-out with preserved model/usage (`09_content_opt_out.py`).
`DIFY_USE_FIXTURES=1` forces the local server even when a Dify endpoint is set.
The scripts still export traces to the configured Respan destination.

Only the adapter uses an editable checkout; core Respan packages remain released
PyPI distributions. The published Dify SDK is 0.1.10. To exercise the optional
async, Knowledge Base, and Workspace scenarios against the separately tested
official 0.1.12 source revision, install it explicitly:

```bash
.venv/bin/python -m pip install \
  'dify-client @ git+https://github.com/langgenius/dify-python-sdk.git@a3ce501021906e23535c268f0b60fea3864864a6'
DIFY_USE_FIXTURES=1 .venv/bin/python run_all.py
```

Use the exact run marker for scoped Respan MCP tree and full-record inspection.
A successful example run alone does not verify stored content, usage or errors.
