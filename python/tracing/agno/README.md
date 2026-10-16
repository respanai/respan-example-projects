# Agno Respan Integration Examples

These examples demonstrate Agno tracing with `respan-instrumentation-agno`.
Each script wraps the Agno run in a unique Respan workflow so the result is
recognizable in the trace list.

## Setup

Install dependencies:

```bash
cd python/tracing/agno
pip install -r requirements.txt -e ../../../../respan/python-sdks/instrumentations/respan-instrumentation-agno
```

Use the repository root `.env` with `RESPAN_API_KEY` set. The editable path
assumes sibling checkouts; substitute your adapter worktree path as needed.
Until the adapter changes are released, install requirements and the local
adapter in the same resolver operation above. Core Respan dependencies remain
released packages from PyPI.

The examples route OpenAI-compatible model calls through Respan, so `RESPAN_API_KEY` is enough.

## Examples

| Example | Workflow name | Description |
|---------|---------------|-------------|
| `01_hello_world.py` | `agno_01_hello_world` | Bare-minimum Agno agent call |
| `02_gateway.py` | `agno_02_gateway` | Respan gateway routing |
| `03_tracing.py` | `agno_03_tracing_workflow` | Respan workflow and task decorators around Agno |
| `04_respan_params.py` | `agno_04_respan_params` | Customer, thread, metadata, and custom identifiers |
| `05_tool_use.py` | `agno_05_tool_use` | Agno agent with a Python tool |
| `06_team.py` | `agno_06_team` | Agno team run |
| `07_streaming.py` | `agno_07_streaming` | Sync/async streams and early close |
| `08_confirmation_and_error.py` | `agno_08_confirmation_and_error` | Synthetic confirmation, continuation, and expected provider error |

Run any example:

```bash
python 01_hello_world.py
```

## Further reading

- [respan-instrumentation-agno](https://pypi.org/project/respan-instrumentation-agno/)
- [respan-ai](https://pypi.org/project/respan-ai/)
- [Agno documentation](https://docs.agno.com/)

Run all eight scripts with one exact marker and deterministic model responses:

```bash
AGNO_USE_FIXTURES=1 RESPAN_EXAMPLE_RUN_ID=your-exact-marker python run_all.py
```

Fixture mode uses real released Agno/OpenAI request serialization and response
parsing with a local HTTP transport. It does not make live model-provider calls;
traces are still exported to the configured Respan endpoint. The final example
always uses fixtures and confirms only its synthetic weather tool. Agno's own
telemetry is disabled in these examples. Omit `AGNO_USE_FIXTURES` to exercise the
configured gateway in the other examples.

Validated SDK versions: Agno 2.6.5 and 3.1.1. No OpenInference adapter is required.
