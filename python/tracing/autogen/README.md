# AutoGen tracing examples

Run real released AutoGen SDK operations with deterministic OpenAI HTTP
responses. Provider calls stay local; traces go to your configured Respan
endpoint. No provider credential or credits are needed.

```bash
cd python/tracing/autogen
pip install -r requirements.txt
python run_all.py
```

Set `RESPAN_API_KEY` in the repository root `.env`. `RESPAN_BASE_URL` defaults to
`https://api.respan.ai/api`. Each script preserves an explicitly supplied
`RESPAN_EXAMPLE_RUN_ID` and attaches it as `metadata.run_id` and
`custom_identifier`. Auto-instrumentation is disabled so the AutoGen adapter
owns the model spans.

For local adapter development, keep the released core dependencies and install
only the target package editable:

```bash
pip install -e ../../../../respan/python-sdks/instrumentations/respan-instrumentation-autogen
RESPAN_EXAMPLE_RUN_ID=autogen-local-a1 python run_all.py
```

| Script | Coverage |
| --- | --- |
| `01_assistant_run.py` | Assistant completion, typed structured output and zero value |
| `02_tool_use.py` | Tool schema/ID, zero result, reflection/history and handled tool error |
| `03_round_robin_team.py` | Two-agent team, native result and saved state |
| `04_stream_lifecycle.py` | Completion, explicit close, read error and cancellation |
| `05_privacy_and_suppression.py` | Private stream handoff, private tool, scoped suppression and visible sibling |
| `06_agent_as_tool.py` | Latest nested AgentTool API and agent/tool/model parentage |
| `07_provider_error.py` | Real SDK HTTP401 error without fabricated output or usage |

The default suite runs seven scripts and emits **41 spans across seven traces**
on AutoGen 0.7.5. Expected counts: 18 chat, 11 agent, eight workflow (including
one team), and four tool spans. Five spans carry controlled OTel errors: one
tool failure, two stream failures/cancellation, and the provider chat/agent pair.
Streaming close/error paths do not fabricate final output or token usage.

Examples pin current AutoGen 0.7.5 and OI AgentChat 0.1.21. The adapter's verified
modern minimum is AutoGen 0.5.1; the latest AgentTool example needs 0.7.5. The old
0.4.0 claim cannot resolve against published OI AgentChat dependencies.

## Legacy families

Use a separate environment for each extra. They share the `autogen` namespace.
The modern default runner does not import legacy SDKs.

```bash
# Python 3.11 for the exact pyautogen 0.2.2 minimum:
pip install -r requirements-legacy-pyautogen.txt
RESPAN_LEGACY_FAMILY=pyautogen python 08_legacy_chat_and_tools.py

# In another environment:
pip install -r requirements-legacy-autogen.txt
RESPAN_LEGACY_FAMILY=autogen python 08_legacy_chat_and_tools.py
```

The legacy script exercises sync/async chat, native history, zero-valued tools
and controlled tool failures with `llm_config=False`. Legacy provider model
tracing requires the matching provider instrumentor. These old API families are
deliberately distinct from the newer packages carrying the same distribution names.

Local fixture success and an HTTP200 export do not establish stored-trace
acceptance. Inspect the exact run in Respan for connected trees, content policy,
current tool calls, errors, reported usage and duplicates. Preserve canonical
OTel error status even if a backend projects it differently.
