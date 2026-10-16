# Strands Agents tracing examples

These scripts run released Strands agent and provider code with controlled HTTP
responses by default. They need no credentials and send no traces or model
requests to a service. Install the portable requirements and run:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
RESPAN_EXAMPLE_RUN_ID=strands-check python run_all.py
```

The suite covers a basic agent, native tool execution, propagated attributes,
structured output, provider failure, the native async event stream, a two-agent
graph, content opt-out, a complete 4096-value vector returned by a tool, native
memory telemetry, and the OpenAI Responses provider. The last two scripts print
an explicit skip when their API is unavailable in the installed Strands version.
Memory telemetry uses the SDK's native tracer with controlled entries; it does
not validate a remote memory store or retrieval model. Vectors are tool results,
not provider embeddings.

`run_all.py` uses one exact marker, continues after a child fails or times out,
and exits nonzero if any child fails. Every initialized Respan instance flushes
and shuts down in `finally`. `RESPAN_EXAMPLE_RUN_ID` from the shell takes priority
over the repository `.env`.

For a live Gateway run of scripts 01–09, set `RESPAN_STRANDS_LIVE=1`. Configure
`RESPAN_API_KEY` in the shell or repository `.env`. `RESPAN_BASE_URL` defaults to
`https://api.respan.ai/api`, and `RESPAN_STRANDS_MODEL` defaults to `gpt-4o-mini`.
The controlled error remains directed at an unreachable local address. A live
structured/tool run depends on the configured model's support. Script 11 always
uses its controlled Responses HTTP fixture.

To export controlled fixture traces to Respan, set `RESPAN_STRANDS_EXPORT=1`
with `RESPAN_API_KEY`; model requests still use the local HTTP fixtures. This is
a separate operation from running the default offline suite.

For local development, install the instrumentation after the requirements:

```bash
pip install -e ../../../../respan/python-sdks/instrumentations/respan-instrumentation-strands-agents
```
