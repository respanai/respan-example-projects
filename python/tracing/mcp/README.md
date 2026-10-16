# Respan MCP Instrumentation Examples

Runnable examples for `respan-instrumentation-mcp`.

The examples load `RESPAN_API_KEY` from the repo root `.env` file and export traces to Respan. Each client script wraps its MCP session in a stable workflow name and uses the same value as `trace_group_identifier`, so traces can be found by workflow name. Set `RESPAN_EXAMPLE_RUN_ID` to attach one exact batch marker to every example while retaining a separate per-example invocation ID.

The examples use released MCP Python SDK 2.3.0 or newer in the 2.x line and
its `MCPServer` API. The paired instrumentation update also supports SDK 1.27.
The stdio tool example asserts that the server receives the workflow trace ID;
the server uses upstream OpenInference context propagation.

## Setup

```bash
cd python/tracing/mcp
pip install -r requirements.txt
```

For local development against this checkout:

```bash
RESPAN_REPO=/path/to/respan
pip install -e "$RESPAN_REPO/python-sdks/instrumentations/respan-instrumentation-mcp" \
            "mcp>=2.3,<3" python-dotenv
```

## Examples

| Example | Workflow name | Description |
|---------|---------------|-------------|
| `01_tool_call_workflow.py` | `mcp_tool_call_workflow` | Lists tools and calls `summarize_city`. |
| `02_resource_read_workflow.py` | `mcp_resource_read_workflow` | Lists resources and reads `profile://city/paris`. |
| `03_prompt_fetch_workflow.py` | `mcp_prompt_fetch_workflow` | Lists prompts and fetches `city_research_prompt`. |
| `04_connection_failure_workflow.py` | `mcp_connection_failure_workflow` | Records a deliberate startup failure with diagnostic content. |
| `05_client_input_continuation.py` | `mcp_input_continuation_workflow` | Uses the high-level MCP 2 client, resumes a tool input request, and records a protocol tool error. |
| `06_resource_prompt_continuations.py` | `mcp_resource_prompt_continuations` | Resumes modern resource and prompt input requests. |

Run an example:

```bash
RESPAN_EXAMPLE_RUN_ID=mcp-audit-001 python 01_tool_call_workflow.py
```

Run all six scenarios with one marker:

```bash
RESPAN_EXAMPLE_RUN_ID=mcp-audit-001 python run_all.py
```

The six scenarios produce 26 spans across six traces. All protocol operations
are local and deterministic. The suite exports their
synthetic inputs, outputs, continuation state, and controlled errors to the
configured Respan destination. There is no model-provider request. Verify stored
traces using an exact `metadata__run_id` MCP filter, then inspect trees and full
log details for parentage, canonical tool/task types, protocol wire aliases,
continuation inputs and error status. A successful runner does not establish
backend semantic acceptance.
