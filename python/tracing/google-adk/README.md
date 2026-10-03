# Google ADK tracing examples

The complete suite runs Google ADK 2.11 with deterministic local models. It sends
synthetic traces to Respan without calling a model provider.

| Script | Coverage |
| --- | --- |
| `01_hello_world.py` | Agent/model response |
| `02_tool_use.py` | Tool call, execution ID and follow-up history |
| `03_respan_attributes.py` | Customer/thread/metadata propagation |
| `04_streaming.py` | SSE events and explicit early close |
| `05_parallel_agents.py` | Parallel agents with separate model spans |
| `06_model_error.py` | Controlled model exception |
| `07_workflow_confirmation.py` | Workflow pause, user confirmation and resumed tool execution |
| `08_workflow_abort.py` | In-flight node cancellation with `abort_signal` |
| `09_model_consult.py` | ModelConsultTool success and adviser error without invented usage |

## Install

Use Python 3.11–3.13. Before the companion adapter update is released, install
requirements and the local adapter in one resolver operation:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -e /absolute/path/to/respan/python-sdks/instrumentations/respan-instrumentation-google-adk
```

Core packages remain released dependencies; editable core checkouts are not
needed. After the adapter release, `pip install -r requirements.txt` is sufficient.

Set `RESPAN_API_KEY` in the repository root `.env` or in the environment.
`RESPAN_BASE_URL` defaults to `https://api.respan.ai/api`. Existing environment
values take precedence over `.env`.

```bash
RESPAN_ADK_MODEL_MODE=local RESPAN_EXAMPLE_RUN_ID=google-adk-my-audit python run_all.py
```

The runner uses a shared exact `metadata.run_id` and one process per script.
Inspect this marker through Respan MCP to check the stored trees and details.
Synthetic prompts, model responses, tool arguments/results, confirmation data
and controlled errors are exported to Respan. No Google credential is needed.

The first three scripts can also use the existing gateway path: install
`litellm`, select `RESPAN_ADK_MODEL_MODE=gateway`, and configure
`RESPAN_GATEWAY_API_KEY`/`RESPAN_GATEWAY_BASE_URL` and `RESPAN_MODEL`. The other
scripts deliberately use local models and protocol fixtures. Live-provider
access and model capability combinations are separate checks.

The new Workflow/ModelConsult scripts require ADK 2.11. Adapter compatibility
with legacy ADK 1.5 is exercised by the adapter's released-SDK tests using
OpenInference 0.1.12; OpenInference 1.x requires ADK 2.10 or newer.
