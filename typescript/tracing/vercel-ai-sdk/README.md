# Vercel AI SDK TypeScript

Gateway-first examples for `ai@7.x` with `@respan/instrumentation-vercel`.

Set `RESPAN_API_KEY` in `respan-example-projects/.env`. Optional overrides: `RESPAN_GATEWAY_API_KEY`, `RESPAN_GATEWAY_BASE_URL`, `RESPAN_BASE_URL`, `RESPAN_MODEL`, `RESPAN_EMBEDDING_MODEL`.

Run:

```bash
npm install
npm run all
```

Examples:

- `01_generate_text.mjs`: `generateText` chat telemetry.
- `02_tool_call.mjs`: tool call loop with `stopWhen` and `prepareStep`.
- `03_embed.mjs`: single embedding call.
- `04_stream_text.mjs`: streaming text generation.
- `05_generate_object.mjs`: structured object generation.
- `06_embed_many.mjs`: batch embeddings.
- `07_tool_loop_agent.mjs`: `ToolLoopAgent` with a deterministic tool.
- `08_audio.mjs`: speech, transcription, streaming transcription, a controlled failure, and content opt-out through the real AI SDK 7.0.126 telemetry adapter. Uses official mock providers; no provider API key or audio service is needed. Audio spans contain text and audio size/format descriptors, because the adapter does not emit audio bytes.

Run `npm run audio` for the five deterministic audio scenarios. `RESPAN_EXAMPLE_RUN_ID` sets a shared `metadata.run_id` marker for platform verification. These examples link the sibling Respan checkout; build its tracing, core, and Vercel instrumentation packages before running them.
