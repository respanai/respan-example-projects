# OpenInference tracing examples

These examples use released OpenInference and OpenAI SDKs with controlled HTTP
responses and native decorators. They make no provider API calls. The default
run keeps spans in memory; Respan export requires an explicit flag.

The nine scripts cover canonical chat/provider fields, complete tool schemas
and invocation IDs, a 5,000-dimensional tool result and embedding, native errors,
streaming, credential redaction, start/end content vetoes, multimodal content,
cache/reasoning usage, and native retriever/reranker/guardrail/evaluator decorators.
The current SDK run produces nine trees and 26 spans. The newer decorators are
explicitly skipped by the minimum OpenInference 0.1.32 runtime.

```bash
cd python/tracing/openinference
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
RESPAN_EXAMPLE_RUN_ID=openinference-local python run_all.py
```

To validate local adapter changes, overlay only the target adapter on released
tracing dependencies:

```bash
python -m pip install -e /absolute/path/to/respan/python-sdks/instrumentations/respan-instrumentation-openinference
python -m pip check
```

To export controlled fixture data to the configured Respan account:

```bash
RESPAN_EXAMPLE_EXPORT=1 \
RESPAN_EXAMPLE_ENV_FILE=/absolute/path/to/respan-example-projects/.env \
RESPAN_EXAMPLE_RUN_ID=openinference-export-unique-marker \
python run_all.py
```

The `.env` file supplies `RESPAN_API_KEY` and optionally `RESPAN_BASE_URL`. Shell
values take precedence. The runner preserves one exact marker, enforces a
per-script timeout, continues after failures, and returns nonzero on any failure.
`RESPAN_EXAMPLE_WIRE_DIR` optionally saves local canonical span records and HTTP
acknowledgments for comparison with scoped Respan MCP results. HTTP acceptance
and trace presence alone do not establish stored-payload correctness.

Validated current releases: OpenInference instrumentation 0.1.70, semantic
conventions 0.1.41, OpenAI instrumentor 0.1.63, OpenAI SDK 2.54.0. Minimum runtime:
OpenInference core/semconv/OpenAI instrumentor 0.1.32, OpenAI 1.78.0, Respan tracing
2.16.1, SDK 2.7.6 and OTel 1.38.0/semantic conventions 0.59b0. Individual delegates
must satisfy their own SDK requirements; this set does not validate every
OpenInference instrumentor. Live provider credentials and services are not part
of the controlled run.
