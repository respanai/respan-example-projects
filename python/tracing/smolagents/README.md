# smolagents tracing examples

These ten scenarios use released smolagents interfaces and deterministic model responses by default. They exercise CodeAgent and ToolCallingAgent, local and managed tools, planning, parallel tool IDs, model streaming, conversation continuation, full RunResult objects, controlled failures, content opt-out, and partial stream closure.

```bash
python -m pip install -r requirements.txt
export RESPAN_API_KEY="your-trace-export-key"
export RESPAN_EXAMPLE_RUN_ID="smolagents-your-run-id"
python run_all.py
```

`.env` is loaded from the repository root with `override=False`, so explicit environment variables win. The runner passes one run ID to every child, applies a timeout to each scenario, runs all scenarios after failures, and exits nonzero if any scenario fails. Trace export uses `RESPAN_BASE_URL`, defaulting to `https://api.respan.ai/api`.

| Script | Coverage |
| --- | --- |
| `01_code_agent.py` | Code generation, local execution, and a city fact tool |
| `02_tool_calling_agent.py` | Function tool definitions, arguments, results, and invocation IDs |
| `03_expected_tool_failure.py` | A controlled native tool exception |
| `04_streaming_agent.py` | Streamed agent steps and final output |
| `05_streamed_model_and_tools.py` | Fragmented model tool arguments and stream usage deltas |
| `06_continuation_and_full_result.py` | `reset=False`, retained memory, and native `RunResult` |
| `07_managed_agent.py` | Parent/child agent execution and managed tool invocation |
| `08_planning_and_parallel_tools.py` | Planning plus parallel calls to the same tool |
| `09_privacy_policy.py` | Content disabled at call start and vetoed during a call |
| `10_model_failure_and_stream_close.py` | Native model exception identity and explicit partial stream close |

Fixture usage counts are explicit synthetic response fields used to test mapping. They are not live provider measurements. Fixtures do not establish remote executor, Exa search, or external provider availability.

To use a live model for scenarios 01, 02, and 04, install `smolagents[litellm]`, set `SMOLAGENTS_MODEL_MODE=live`, and supply `RESPAN_GATEWAY_API_KEY` (or `RESPAN_API_KEY`), `RESPAN_GATEWAY_BASE_URL`, and optional `RESPAN_MODEL` (default `gpt-4o-mini`). The other scenarios remain controlled fixtures. This mode requires a configured provider route and available credentials; deterministic results and live usage are not interchangeable.
