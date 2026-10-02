# Exa + Respan (Python)

Feature-compatible examples for `respan-instrumentation-exa` and the released `exa-py==2.20.0` SDK.

The default mode starts a deterministic loopback HTTP server and exercises the real Exa SDK request, response, SSE, Agent, Research, and tool-helper code paths without consuming Exa credits. Set `RESPAN_EXA_LIVE=1` to use `EXA_API_KEY` for the core, streaming, tool, and Agent scenarios. The legacy Research scenario remains loopback-only because Exa deprecates `/research/v1` in favor of `search(type="deep-reasoning")`.

## Setup

```bash
cd python/tracing/exa
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The repository-root `.env` must contain `RESPAN_API_KEY`. `RESPAN_BASE_URL` is optional. Live mode also requires `EXA_API_KEY`.

## Run

```bash
.venv/bin/python run_all.py
```

The suite uses one `RESPAN_EXAMPLE_RUN_ID` for exact platform lookup and runs:

- core search, contents, and grounded answer
- sync search streaming plus async search/answer streaming
- provider-neutral `web_search` and Python 2.20 `get_contents` tools
- Agent `create_and_wait` and loopback legacy Research compatibility
- a controlled provider error span in loopback mode

Acceptance requires inspecting the scoped Respan trace trees and individual spans, including inputs/outputs, citations in `respan.metadata`, bare `llm` naming when the answer API supplies no model, error status, stream completion, provider-neutral entity names, hierarchy, and duplicate absence. Local exit code or exporter logs alone are not acceptance.
