# Helicone + Respan TypeScript examples

These deterministic examples exercise `@respan/instrumentation-helicone`
against the public `@helicone/helpers` 1.8.3 runtime.

The suite covers:

- `logRequest` chat content, tool definitions/tool calls, and provider usage
- `logStream` and `logSingleStream` aggregation
- `logSingleRequest`, direct `sendLog`, and `HeliconeLogBuilder`
- builder success/error status, `addAdditionalHeaders`, and `toReadableStream`
- Helicone custom `tool`, `vector_db`, and `data` events
- Anthropic content blocks, `input_schema` tools, tool use, and cache-read usage
- Anthropic SSE, Google candidates/parts, and fragmented OpenAI stream tool calls
- delayed-builder creation parent/correlation retention across a later send context
- `traceContent: false` plus safe constructor-level user/session/property headers
- an operation that fails before Helicone reaches `sendLog`

Helicone logging is directed to an in-process HTTP server. The examples never
need or transmit a Helicone API key, but their Respan spans are exported to the
configured Respan platform for semantic inspection.

## Setup

Add `RESPAN_API_KEY` to `respan-example-projects/.env`. `RESPAN_BASE_URL` is
optional. Then run:

```bash
cd typescript/tracing/helicone
npm install
npm run typecheck
RESPAN_EXAMPLE_RUN_ID="helicone-ts-$(date +%s)" npm run examples
```

Every scenario uses the same run id in `custom_identifier` and
`metadata.run_id`. Query the Respan platform with that exact marker and inspect
the complete trees and span bodies, including hierarchy, types, model/provider,
input/output, token usage, tool payloads, custom events, error status, and
duplicates.
