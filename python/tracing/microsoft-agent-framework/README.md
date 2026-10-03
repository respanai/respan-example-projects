# Microsoft Agent Framework tracing examples

Seven local fixture scripts exercise Agent Framework 1.20.0 and the paired instrumentation update. The adapter also supports 1.8.1, subject to the upstream stream limitations below.

```bash
pip install -r requirements.txt
pip install --no-deps -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-microsoft-agent-framework
RESPAN_EXAMPLE_RUN_ID=maf-audit-001 python run_all.py
```

Set `RESPAN_API_KEY` in the repository root `.env` or environment. `RESPAN_BASE_URL` defaults to `https://api.respan.ai/api`. The default suite uses real framework classes with deterministic provider results and exports synthetic trace payloads to Respan. It makes no model-provider requests. All scenarios carry the exact marker in `metadata.run_id` and a workflow-specific custom identifier.

| Script | Coverage |
|---|---|
| `01_agent_tool_workflow.py` | Native workflow, agent, tool call, historical/current call separation and response usage. |
| `02_deterministic_failure.py` | A native tool exception. |
| `04_stream_lifecycle.py` | Stream completion, early close, failure and cancellation. |
| `05_content_privacy.py` | Scoped content opt-out for chat, stream and tool spans. |
| `06_falsy_tools.py` | False and zero tool results through typed Content responses and subsequent chat history. |
| `07_scoped_suppression.py` | Suppressed native activity between two visible calls. |
| `08_embeddings.py` | Full 128-value vectors, reported/absent usage, private embedding and controlled failure. |

`03_live_agent_tool_workflow.py` is an optional live Gateway example. It runs only when `RESPAN_MAF_RUN_LIVE=1`; configure `RESPAN_GATEWAY_API_KEY`, `RESPAN_GATEWAY_BASE_URL`, and optional `RESPAN_MODEL` for that separate run.

The default runner produces 32 spans across seven connected traces. Inspect the exact `metadata__run_id` through Respan MCP, then inspect all trees and detailed records for usage, vectors, tool IDs, privacy, suppression, parentage and errors. Source framework spans and current-turn tool calls should not be duplicated.

Agent Framework 1.8.1 has no public `ResponseStream.close()` and leaves cancelled native chat spans unfinished even without Respan. The full example runner therefore targets current 1.20.0. Native response objects and iterator behavior are preserved by the adapter.
