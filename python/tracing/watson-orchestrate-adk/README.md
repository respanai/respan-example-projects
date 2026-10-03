# Watson Orchestrate ADK tracing

Python examples for `ibm-watsonx-orchestrate` **2.18.0** and
`respan-instrumentation-watson-orchestrate-adk`.

```bash
pip install 'ibm-watsonx-orchestrate==2.18.0' respan-ai \
  respan-instrumentation-watson-orchestrate-adk python-dotenv
export RESPAN_API_KEY=...
export RESPAN_EXAMPLE_RUN_ID=watson-my-run
python run_all.py
```

Install the companion adapter branch before release to exercise the new
coverage. Only that adapter needs an editable install; Respan core dependencies
come from the registry. The runner preserves the exact marker, bounds each
script to 90 seconds, continues after a failure, and exits nonzero if any
script fails.

| Script | Coverage |
| --- | --- |
| `01_local_agent_tool.py` | Real local tool success and controlled failure |
| `02_run_client.py` | Real SDK run submission and thread correlation |
| `03_watsonx_chat.py` | System instructions, response model, provider usage |
| `04_async_run.py` | Real WebSocket event handling and cleanup |
| `05_expected_error.py` | Controlled provider 429, preserved exception |
| `06_live_run_client.py` | Optional live IBM run submission |
| `07_live_watsonx_chat.py` | Optional live watsonx.ai inference |
| `08_current_sdk_features.py` | Files, polling, returned failures, WebSocket callbacks, Groq/Gateway, tool-only responses, zero usage, architect/CPE, flows |
| `09_content_policy.py` | Environment/runtime content opt-out and OTel suppression |

The default suite replaces HTTP/WebSocket transports, leaving instrumented SDK
methods intact. It needs a Respan key but no IBM credentials. All provider
responses are synthetic. Scripts 06 and 07 require `RESPAN_WATSON_LIVE=1` as
well as their service credentials, and otherwise print an explicit skip.

For live runs, configure `WATSON_ORCHESTRATE_BASE_URL`,
`WATSON_ORCHESTRATE_API_KEY`, and `WATSON_ORCHESTRATE_AGENT_ID`; optionally set
`WATSON_ORCHESTRATE_THREAD_ID`, `WATSON_ORCHESTRATE_IS_LOCAL`, and
`WATSON_ORCHESTRATE_VERIFY_SSL`. Live watsonx.ai uses `WATSONX_APIKEY` and
`WATSONX_SPACE_ID` (and optional `WATSON_ORCHESTRATE_LLM_MODEL`).

Inspect only the exact `metadata.run_id` after a run, then inspect each trace's
span tree and relevant full log records. Expect current-turn tool calls only,
zero provider usage preserved, failed run spans marked ERROR, nested tool
parentage, and no content on the two policy-disabled children. The suppressed
call must have no child span. Local assertions and successful export are
separate from stored-trace acceptance; report any ingestion differences.
