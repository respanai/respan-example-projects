# Vercel AI SDK for Python tracing examples

Run the real Vercel `ai==0.8.0` SDK through the local Respan instrumentation and export the traces to Respan. Deterministic scenarios use the SDK's `FakeModel` and a local provider; `--live` also sends one text request through the Respan Gateway.

Use Python 3.12 or 3.13. Install the local instrumentation checkout first while its release is pending:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-vercel
pip install -r requirements.txt
python run_all.py --env-file /path/to/.env --run-id vercel-python-unique-run --live
```

The env file must contain `RESPAN_API_KEY`. Optional settings are `RESPAN_BASE_URL` for trace ingestion and `RESPAN_EXAMPLE_MODEL` for the live Gateway request (default `gpt-4o-mini`). Keep credentials out of the generated artifacts.

The suite covers text generation and streaming, agent tools and `current_tool_call()`, structured output, multimodal messages, seven non-chat operations, typed Noul evaluation, expected provider errors, hooks, durable replay, and runtime/instrumentor content opt-outs. It uses the 0.8 `ai.ops.experimental.evaluate` API with both mapped questions and Pydantic question/output models.

`--output verification.json` records the SDK version, scenario results, and trace/span IDs. A companion `.otlp.json` file preserves the synthetic example payloads sent to Respan. A successful run confirms execution and export attempts; inspect these exact traces using Respan MCP to verify ingestion, parentage, usage, and content.

For an offline check without credentials or export, run `python run_all.py --no-export`. The `.spans.json` artifact contains the locally captured spans for inspection.
