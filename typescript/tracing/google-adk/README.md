# Google ADK TypeScript tracing

Six controlled scenarios exercise the released Gemini SDK and ADK's native runner, model, tool, streaming, and graph paths. The default transport supplies local provider responses through `fetch`. No Gemini key or Respan export is required.

## Run

Build the local `respan/javascript-sdks/instrumentations/respan-instrumentation-google-adk` package first, with the `respan` and `respan-example-projects` repositories beside each other. Then:

```bash
npm ci
npm run typecheck
npm run all
```

Only the adapter is installed from local source. Tracing and SDK companions use pinned released versions. `.npmrc` sets `install-links=true` so npm installs a copy of the package.

- `01:hello`: native Gemini runner, agent, and chat.
- `02:tool`: tool schema, parallel model calls, both tool results, and call ID correlation.
- `03:streaming`: native Gemini streaming aggregation and propagated attributes.
- `04:graph`: ADK 2.2.1 `Workflow` and `FunctionNode`, including node paths.
- `05:privacy`: content disabled for the adapter.
- `06:error`: controlled provider 429 represented by ADK's native error event.

Each script initializes tracing before importing ADK and shuts it down after flushing. The graph example requires ADK 2.x; this API does not exist at the adapter's supported minimum, ADK 1.2.0.

## Optional export and live provider

Set `RESPAN_EXAMPLE_EXPORT=1` and `RESPAN_API_KEY` to export the controlled traces. `RESPAN_BASE_URL` optionally selects the Respan service. Set `RESPAN_EXAMPLE_RUN_ID` to correlate a run; `RESPAN_EXAMPLE_PROFILE` and `RESPAN_EXAMPLE_SOURCE_HASH` add validation metadata.

For a local capture-and-forward collector, set `RESPAN_EXAMPLE_TRACE_URL` to its OTLP/HTTP endpoint. `RESPAN_CAPTURE_FILE` optionally records final span IDs, parents, attributes, and exporter receipts as JSON lines. The runtime performs its normal semantic export cleanup before that exporter receives spans.

`GOOGLE_ADK_LIVE=1` explicitly enables live Gemini calls and requires `GOOGLE_GENAI_API_KEY`. Keep it unset for the controlled suite. The error scenario intentionally uses the local provider fixture; its span status reflects what ADK actually emits.
