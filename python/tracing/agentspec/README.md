# AgentSpec tracing examples

Nine deterministic examples exercise AgentSpec 26.3.1 and its real LangGraph
adapter. A local LangChain model supplies fixture responses; a local tool
performs subtraction. The scripts never call a live model provider. Only
synthetic traces are sent to Respan.

## Setup

Set `RESPAN_API_KEY` in the repository root `.env`. Optional `RESPAN_BASE_URL`
defaults to `https://api.respan.ai/api`. Existing environment values are preserved.
No provider API key is needed.

```bash
cd python/tracing/agentspec
pip install -r requirements.txt
```

Before the companion adapter update is released, install the adapter checkout
and requirements together, keeping all core dependencies released:

```bash
pip install -r requirements.txt \
  -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-agentspec
```

## Run

```bash
RESPAN_EXAMPLE_RUN_ID=agentspec-my-run python run_all.py
```

| Script | Coverage |
| --- | --- |
| `01_haiku_agent.py` | Basic agent request with deterministic fixture output |
| `02_agent_with_tool.py` | Correlated tool call, zero result, follow-up model call |
| `03_propagated_attributes.py` | Thread/metadata propagation and separate sequential inputs |
| `04_async_agents.py` | Concurrent async agents and async tool execution |
| `05_streaming.py` | Public sync/async message streams with final zero usage |
| `06_tool_flow.py` | Native FlowBuilder, explicit data edges, sync/async local tool |
| `07_content_policy.py` | Environment/context content policy and standard suppression |
| `08_controlled_errors.py` | Original model/tool errors, synchronous and asynchronous |
| `09_sensitive_mask.py` | AgentSpec sensitive-information masking, including callback fields |

The non-streaming fixture reports zero input tokens, three output tokens,
zero cached input tokens and two reasoning tokens. Streaming reports a final
zero/zero usage record. These are fixture-provided values, not estimates.
The current AgentSpec tool graph returns the native final value `0.0`; its
model span retains the actual follow-up response `answer 0.0`.

`run_all.py` applies one marker to all subprocesses, fails if any scenario fails,
and each script shuts down its Respan instance. The full suite targets 26.3.1;
FlowBuilder is unavailable in the adapter's separately tested 26.1.0 minimum.
The legacy filenames remain usable, but their default execution now uses local
fixtures instead of the gateway.

Local success does not establish stored-trace correctness. Query the exact
`metadata__run_id` through the Respan MCP, inspect every tree, and compare model
messages, usage, tool IDs/results, privacy and errors with the exported payload.
