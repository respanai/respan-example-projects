# BeeAI TypeScript tracing examples

Use BeeAI Framework 0.1.31 with `@respan/instrumentation-beeai`. The instrumentor
captures native agents, models, tools, streams, structured output, and embeddings.
The manifest uses published Respan 2.5.0, tracing 1.6.1, and SDK 1.3.4, with only
the BeeAI instrumentor linked to the sibling SDK repository.

## Setup

```bash
cd typescript/tracing/beeai
npm install
```

Set `RESPAN_API_KEY` in the repository root `.env` file or your environment.
`RESPAN_BASE_URL` optionally selects the trace destination.

The live chat and agent examples also use `RESPAN_GATEWAY_API_KEY` (defaults to
`RESPAN_API_KEY`), `RESPAN_GATEWAY_BASE_URL` (defaults to
`https://api.respan.ai/api`), and `RESPAN_MODEL` (defaults to `gpt-4o`).

## Run

```bash
npm run basic
npm run tools
npm run native
npm run all
```

- `basic`: one live BeeAI OpenAI chat request through the Respan gateway.
- `tools`: a live `RequirementAgent` using the calculator tool.
- `native`: eight controlled workflows using the released BeeAI OpenAI adapters
  with deterministic HTTP responses. Covers 75 messages, complete tool schemas,
  historical and current tool calls, agent and tool IDs, streaming callbacks,
  a 5001-dimensional vector, false/zero/empty tool outputs, structured output,
  provider errors, and content privacy. Provider calls stay within the controlled
  fetch boundary; traces are exported to the configured Respan destination.

BeeAI 0.1.31's RequirementAgent imports `uuid` without declaring it. The example
manifest includes `uuid` so a clean install can run that native agent.

The controlled suite also adapts to BeeAI 0.1.9's `ToolCallingAgent`, tool-result
shape, and structured generation API for minimum-version audits.

Set `RESPAN_EXAMPLE_RUN_ID` to correlate the complete run. Every workflow carries
that value as `custom_identifier` and `metadata.run_id`, plus its workflow name.
For long indexed message histories, configure the OpenTelemetry
`OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT` above the default 128 attributes; the full
history remains available in the entity input.
