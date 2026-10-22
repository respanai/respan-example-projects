# Pydantic AI Respan Integration Examples

These examples demonstrate how to integrate `pydantic-ai` v2 with Respan tracing using `respan-ai` and `respan-instrumentation-pydantic-ai`.

## Setup

1. Install the paired local instrumentation update and current SDK requirements in
one resolver operation. Keep the Respan core packages on their released versions:

```bash
cd python/tracing/pydantic-ai
python -m pip install -r requirements.txt \
  -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-pydantic-ai
```

Use this editable adapter until the companion SDK change is published. The
requirements pin AI semantic conventions 0.5.1, which resolves the current
PydanticAI 2.54 / Respan facade dependency set. The full PydanticAI distribution
installs Logfire 5.1.1 and requires OpenTelemetry SDK below 1.45; use a separate
environment from integrations that require 1.45 or later.

2. Use the repository root `.env` values:

```bash
RESPAN_API_KEY=...
RESPAN_BASE_URL=https://api.respan.ai/api
RESPAN_GATEWAY_BASE_URL=https://api.respan.ai/api
RESPAN_GATEWAY_API_KEY=...
PYDANTIC_AI_GATEWAY_MODEL=gemini/gemini-2.5-flash
PYDANTIC_AI_ANTHROPIC_GATEWAY_MODEL=claude-sonnet-4-5-20250929
```

The examples use Pydantic AI's real deterministic `TestModel` runtime by default so the complete native agent/chat/tool tree is repeatable. Set `RESPAN_PYDANTIC_LIVE=1` to use an explicit `OpenAIChatModel` through the configured Respan gateway. Model selection is `PYDANTIC_AI_GATEWAY_MODEL`, then `RESPAN_VERTEX_GATEWAY_MODEL`, then `RESPAN_MODEL`. The Anthropic example uses `PYDANTIC_AI_ANTHROPIC_GATEWAY_MODEL` on that opt-in live path.

## Examples

| Example | Description |
|---------|-------------|
| `01_hello_world.py` | Bare-minimum sanity check — instrument + one agent call |
| `02_gateway.py` | Gateway pattern with content capture options |
| `03_tracing.py` | Workflow/task spans with `@workflow` and `@task` decorators |
| `04_respan_params.py` | Setting `customer_identifier`, `metadata`, and `custom_tags` on spans |
| `05_tool_use.py` | Tracing a Pydantic AI agent that uses tools |
| `06_anthropic.py` | Running Anthropic models through the Respan gateway |
| `07_embeddings.py` | Native sync query, async document embeddings, full 128-dimension vectors, controlled failure |
| `08_structured_and_streaming.py` | Structured output, async stream completion and failure, current version 6 telemetry |
| `09_content_opt_out.py` | Agent and embedding content disabled while retaining model/usage |

Run any example:

```bash
python 01_hello_world.py
```

Run the full exact-marker set:

```bash
RESPAN_EXAMPLE_RUN_ID=otel2-pydantic-ai-check python run_all.py
```

## How it works

1. `Respan(...)` initializes the OpenTelemetry pipeline for Respan.
2. `PydanticAIInstrumentor()` enables native `Agent` and `Embedder` OpenTelemetry spans and normalizes them for Respan.
3. The default models run locally. The first six scenarios can opt into `OpenAIChatModel` with the configured Gateway provider; the three feature scenarios always use deterministic native SDK models.
4. Traces, spans, and metrics from LLM calls, tools, and workflows are sent to Respan and visible in the dashboard.

## Further reading

- [respan-ai](https://pypi.org/project/respan-ai/)
- [respan-instrumentation-pydantic-ai](https://pypi.org/project/respan-instrumentation-pydantic-ai/)
- [Respan Documentation](https://docs.respan.ai)
- [Pydantic AI](https://ai.pydantic.dev/)

The runner executes nine scripts with one `RESPAN_EXAMPLE_RUN_ID`; every span
carries exact `run_id` and `example_run_id` metadata. Local model calls do not
contact a provider, but the examples export synthetic traces to Respan. Verify
trees and full log records with that exact marker before treating the run as
semantic acceptance. Native PydanticAI 2.54 leaves the failed streaming model
span unset while recording the error on its agent span; that SDK behavior is
preserved.
