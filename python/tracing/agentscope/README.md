# AgentScope tracing examples

These nine deterministic scripts use real AgentScope agents, models, tools and
pipelines with local models or an HTTP `MockTransport`. They never call a live
model provider. Only traces are exported to Respan.

## Setup

Set `RESPAN_API_KEY` in the repository root `.env`. Optional `RESPAN_BASE_URL`
defaults to `https://api.respan.ai/api`. The loader preserves existing environment
values, including `RESPAN_EXAMPLE_RUN_ID` for exact-run trace queries.

```bash
cd python/tracing/agentscope
pip install -r requirements.txt
```

Before the companion adapter update is released, install this checkout and the
requirements in **one resolver operation**, using released core packages:

```bash
pip install -r requirements.txt \
  -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-agentscope
```

The examples use AgentScope 2.0.9 features. The adapter separately tests its
minimum supported AgentScope 2.0.3.

## Run

```bash
RESPAN_EXAMPLE_RUN_ID=agentscope-my-run python run_all.py
```

| Script | Coverage |
| --- | --- |
| `01_agent_and_model.py` | Direct model call and agent reply |
| `02_tool_call.py` | Model tool call, correlated execution, follow-up answer |
| `03_multi_agent_and_failure.py` | Writer/reviewer observe flow, controlled failure |
| `04_streaming.py` | Real provider parser, agent event stream, explicit early close |
| `05_embeddings.py` | Batching, full 256-value vectors, controlled provider error |
| `06_structured_output.py` | Typed structured-generation path and actual zero usage |
| `07_content_policy.py` | Environment/context privacy, policy snapshot, suppression |
| `08_team_pipeline.py` | Leader-to-member delegation and resumed leader |
| `09_capture_opt_out.py` | Instrumentor payload opt-out with retained usage |

The HTTP fixtures report actual zero chat usage and seven embedding tokens per
batch. Scripted local models provide their declared synthetic fixture usage.
Early close has no final usage to report. The runner fails if any script fails
and shuts down each Respan instance after its scenario. Local success is separate
from stored-trace verification: use the exact run marker with the Respan MCP to
inspect trees, payloads, tool correlation, usage, privacy and exceptional spans.
