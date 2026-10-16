# Strands Agents TypeScript tracing examples

These examples run released Strands `Agent`, `OpenAIModel`, graph, swarm, and MCP
APIs with controlled in-memory OpenAI SSE responses. They capture traces locally
by default and need no API keys. Use Node.js 22 or newer.

Build the instrumentation in the sibling `respan` checkout, then run:

```bash
npm ci
npm run typecheck
npm run all
```

Only `@respan/instrumentation-strands-agents` comes from the local checkout.
Respan companion packages are released registry packages, and `install-links=true`
installs a package copy. The lockfile retains the relative local package path.
Strands' optional telemetry peers use exporter version 0.219; npm installs
Respan's newer exporter separately to satisfy both declared ranges.

The ten scripts cover basic invocation, native model-driven tools, streaming,
structured output, graph, swarm, in-memory MCP tools, content privacy, a controlled
provider error, and 75 messages plus a 5,001-value vector with scalar edge cases.
The privacy script runs the provider normally while omitting trace content.
The error script catches the expected native failure.

Set `RESPAN_EXAMPLE_CAPTURE_DIR` to save local span records. Set
`RESPAN_EXAMPLE_RUN_ID` to attach a shared marker. Captures include the workflow,
trace and span IDs, parent links, attributes, events, and status.

To send controlled example traces to Respan, set `RESPAN_EXAMPLE_EXPORT=true` and
provide `RESPAN_API_KEY`. `RESPAN_BASE_URL` is optional. Export mode reads the
repository root `.env`; local capture does not require it.

To call a live OpenAI provider, set `STRANDS_EXAMPLE_PROVIDER=live` and
`OPENAI_API_KEY`; optionally set `STRANDS_EXAMPLE_MODEL`. Provider calls and
Respan trace export are independent options. The controlled error scenario
always uses its local transport.

```bash
RESPAN_EXAMPLE_CAPTURE_DIR=./captures npm run all
RESPAN_EXAMPLE_EXPORT=true npm run 02:tool
```
