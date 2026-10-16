# Writer TypeScript Tracing Examples

These examples use the real official Writer SDK 3.0.0 with a deterministic HTTP transport. They need `RESPAN_API_KEY` to export controlled traces; no Writer key is required in the default mode. Set `RESPAN_EXAMPLE_RUN_ID` to correlate the run. The examples load `.env` from the `respan-example-projects` repository root.

Place the Respan SDK repository beside this examples repository so the local instrumentation dependency resolves, then run:

```bash
npm ci
npm run typecheck
RESPAN_EXAMPLE_RUN_ID=writer-local-check npm run examples
```

Only `@respan/instrumentation-writer` is local. Respan companion packages are released npm dependencies.

The ten scenarios cover basic chat, event streaming, native structured parsing, explicit application tool execution and tool-result history, text completion, an expected HTTP error, native SSE iteration and early return, raw and paired responses, 75-message history with a 75-property tool schema, and content-disabled capture. Tool execution uses `withTool`; historical messages do not generate new tool execution spans. Raw responses remain unread until the application consumes them.

Set `WRITER_EXAMPLE_MODE=live` and `WRITER_API_KEY` to opt into actual provider requests. Live mode consumes provider resources and is not part of the deterministic default run. Configure `WRITER_MODEL` and `WRITER_COMPLETION_MODEL` for models available to that account. Writer SDK 2.0.0 supports base chat/SSE/completion calls but predates `chat.parse` and the event helper; those two scenarios require a later SDK release.
