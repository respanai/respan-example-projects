# AgentOps tracing examples

All nine examples use released AgentOps 0.4.21 and controlled data. The default
captures spans in memory without loading `.env` or exporting traces.

```bash
cd python/tracing/agentops
python -m pip install -r requirements.txt
python run_all_examples.py
```

| Script | Native feature |
| --- | --- |
| 01 | Workflow, agent, task and actual tool hierarchy |
| 02 | Caught task failure with the original exception |
| 03 | Async workflow, task and tool returns/context |
| 04 | Public trace lifecycle, metadata update and explicit error state |
| 05 | Actual OpenAI HTTP, two current declarations, schemas and executed tools with source IDs |
| 06 | Native SSE, source usage, sync/async 5000-dimensional embeddings |
| 07 | Start privacy bound and context veto, including raw metadata |
| 08 | Input/output guardrails |
| 09 | Native generator send/exhaustion protocol and existing SDK quirks |

Provider cases use real OpenAI 2.44.0 clients with controlled HTTP/SSE transports;
no model-provider credentials or network access are needed. Tool results preserve
full dense 5000-dimensional and sparse 256-entry vectors. The adapter records
current declarations on model spans and actual executions as tool spans.

To export these same synthetic fixtures explicitly:

```bash
RESPAN_EXPORT=1 RESPAN_EXAMPLE_RUN_ID=your-unique-marker python run_all_examples.py
```

Export loads the repository-root `.env` with `override=False`, or the file named
by `RESPAN_ENV_FILE`. Set `RESPAN_API_KEY`; the base URL defaults to
`https://api.respan.ai/api`. All spans carry the marker in Respan metadata for
scoped inspection. Credentials are not printed. Set `AGENTOPS_CAPTURE_DIR` for
local span records and `AGENTOPS_RUNNER_REPORT` for complete runner counts.

The same nine cases run with current dependencies and exact Respan floors
(tracing 2.17.0, SDK 2.7.6, OTel 1.38.0/semantic conventions 0.59b0, AI semantic
conventions 0.5.1). Current and minimum AgentOps versions are both 0.4.21.

AgentOps' native sync generator helper attaches context eagerly, leaves it
attached and consumes generator return values; close/error can leave spans open.
The adapter preserves those upstream behaviors, and the runner isolates each
example in a subprocess. Successful exhaustion is tested. These fixtures do not
validate live model access, AgentOps cloud export/authentication, every provider,
or every agent framework. Configure native provider instrumentors after the
Respan adapter is active.

HTTP acceptance alone does not establish stored semantics. Compare the same-run
wire payloads, complete trees and full records, especially errors, privacy, usage,
tool calls and vectors.

Primary references: [official releases](https://github.com/AgentOps-AI/agentops/releases),
[SDK source](https://github.com/AgentOps-AI/agentops/tree/0.4.21/agentops/sdk), and
[official introduction](https://docs.agentops.ai/v2/integrations/agentssdk).
