# CrewAI tracing examples

Run real CrewAI agents, crews, flows, native OpenAI-backed model calls, and tools
with Respan tracing. The default runner uses deterministic HTTP fixtures and
makes no model-provider requests. It exports synthetic traces to your configured
Respan project.

Tested with CrewAI **1.15.23**, OpenAI **2.54.0**, and released Respan tracing
**2.20.1**. Install requirements and the adapter under review in one resolver
operation until the SDK update has been released:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -e /absolute/path/to/respan/python-sdks/instrumentations/respan-instrumentation-crewai
```

After the adapter update is published, `pip install -r requirements.txt` is
sufficient. The requirements keep Respan core packages on published releases.
CrewAI 1.10.1 is separately tested at the adapter level using released
`respan-tracing` directly; its OpenTelemetry 1.34.x pin conflicts with the current
facade's bundled Together instrumentation. These current-feature examples use
CrewAI >=1.15.23, including `ToolFailure` and public stream sessions.

Set `RESPAN_API_KEY` in the repository-root `.env` or your shell. Optionally set
`RESPAN_BASE_URL` (default `https://api.respan.ai/api`). Explicit shell values are
preserved. CrewAI's independent product telemetry is disabled by default and its
SQLite storage uses a temporary directory.

```bash
RESPAN_EXAMPLE_RUN_ID=crewai-my-review python run_all.py
```

The runner preserves this exact marker, runs all eight scripts in isolated
processes with timeouts, and reports any failures. Every script flushes CrewAI's
background event handlers before shutting down Respan.

| Script | Coverage |
| --- | --- |
| `01_basic_crew.py` | Crew, task, agent, and native model parentage |
| `02_tool_use.py` | Two tools, current call IDs, historical tool messages |
| `03_attributes.py` | Synthetic customer, thread, and metadata attribution |
| `04_native_llm.py` | Sync/async Chat Completions and Responses, zero-token streams, public stream session |
| `05_agent_methods.py` | Direct Agent kickoff and kickoff_async |
| `06_flows.py` | User Flow methods and a controlled failing Flow |
| `07_privacy.py` | Environment/context opt-out, snapshot across await, suppression |
| `08_failures.py` | Provider error and a normally returned typed ToolFailure |

Only the first three examples opt into real model calls with
`CREWAI_USE_LIVE_LLM=1`. Their provider defaults to `respan-gateway`; set
`CREWAI_RESPAN_LLM_PROVIDER=openai` with `OPENAI_API_KEY` for direct OpenAI, or
`anthropic` with `ANTHROPIC_API_KEY` after installing CrewAI's Anthropic extra.
The other scripts always use local fixtures.

The privacy example keeps model metadata and reported usage while omitting
prompt/completion payloads. Failed model calls export OTel ERROR and error
metadata without inventing model output or usage. Stored dashboard fields can
reflect downstream ingestion behavior; compare exact-run span details with the
exported canonical attributes when reviewing an integration.
