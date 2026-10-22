# OpenRouter Python tracing examples

Run native OpenRouter SDK and OpenAI-compatible features through controlled HTTP fixtures. SDK request validation, typed responses and stream parsing remain real. The default runner makes no live provider calls and exports no traces.

## Install and run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_all.py
```

For a local adapter PR, install only that package into the environment:

```bash
pip install -e "$RESPAN_REPO/python-sdks/instrumentations/respan-instrumentation-openrouter[native]"
python run_all.py
```

The native coverage described here requires the companion instrumentation change; use the target-only install above while that change is unreleased. All other Respan dependencies stay released. This group validates native `openrouter==1.3.22`, compatible OpenAI 3.0.0 and 3.24.0, and both declared minimum/current Respan dependencies. OTel semantic conventions 0.66b0 and AI conventions 0.5.1 provide the modern fields.

## Scenarios

| Script | Feature |
| --- | --- |
| 01 | Native chat and provider routing request options |
| 02 | Native synchronous chat stream/context manager |
| 03 | Native function tool schema, current call ID, decorated local execution |
| 04 | Native asynchronous chat |
| 05 | Compatible typed structured-output `parse` |
| 06 | Native asynchronous chat stream/context manager |
| 07 | Actual SDK exception from controlled HTTP 429 |
| 08 | Explicitly enabled live native chat; skipped by default |
| 09 | Stable and beta native Responses |
| 10 | Stable native Responses stream |
| 11 | Native embedding with all 3,072 float values captured |
| 12 | Content opt-out with identities/usage retained |
| 13 | Compatible chat, Responses, text and embedding |
| 14 | Native asynchronous Responses, stream and embedding |
| 15 | Current native web-search server-tool request schema |

The server-tool fixture validates request parsing and captured definitions. It does not execute a real web search. The adapter does not instrument the separate `openrouter-agent-sdk`, native media, rerank or administration endpoints.

## Export and inspect

```bash
export RESPAN_EXAMPLE_RUN_ID="openrouter-audit-unique-marker"
export RESPAN_EXAMPLE_EXPORT=1
export RESPAN_API_KEY="your-respan-key"
python run_all.py
```

This explicitly sends the controlled fixture data to `https://api.respan.ai/api/v2/traces`. Each span carries `run_id`, `example_run_id`, the scenario and example-set metadata. Shell values take precedence over a repository `.env` file. Set `RESPAN_EXAMPLE_REPORT_DIR` to save local OTLP span records.

Filter Respan MCP by the exact `metadata__run_id`; inspect trace trees and full span records for connected workflow/model/tool relationships, input/output, integer usage, complete tools/vectors, stream completion and source-only errors. HTTP export success and local tests do not establish stored-trace semantic acceptance. Backend projection discrepancies must remain visible in the validation report.

Live calls require both `OPENROUTER_EXAMPLE_LIVE=1` and `OPENROUTER_API_KEY`. The presence of a key alone never switches fixture scenarios to live calls. Live provider calls and Respan export are independent opt-ins.

The runner gives every subprocess the same marker, applies a 90-second timeout, runs all scenarios and reports failures together. Clients, streams and tracing processors are closed explicitly.
