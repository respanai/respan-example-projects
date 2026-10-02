# Dify Python Tracing Examples

These examples exercise the first-party `respan-instrumentation-dify` package
with the real `dify-client` Python package.

The scripts load the repo-root `.env` in `respan-example-projects/.env`. If no
`DIFY_BASE_URL` is configured, they start a local Dify-compatible HTTP server so
the full tracing path is runnable with only `RESPAN_API_KEY`.

## Setup

From this directory:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python \
  -e ../../../../respan/python-sdks/respan-sdk \
  -e ../../../../respan/python-sdks/respan-tracing \
  -e ../../../../respan/python-sdks/respan \
  -e ../../../../respan/python-sdks/instrumentations/respan-instrumentation-dify
```

## Run

```bash
.venv/bin/python run_all.py
```

`run_all.py` generates and prints one `RESPAN_EXAMPLE_RUN_ID` and passes it to
all seven child scenarios. Set it explicitly when you want a predetermined
platform audit marker:

```bash
RESPAN_EXAMPLE_RUN_ID=dify-py-audit-001 .venv/bin/python run_all.py
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
