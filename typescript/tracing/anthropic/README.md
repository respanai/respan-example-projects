# Anthropic TypeScript tracing

Eight scripts call the real `@anthropic-ai/sdk` 0.133.0 through controlled HTTP/SSE and JSONL transport fixtures. By default, the released Respan exporter sends spans to a local HTTP collector. No credentials or `.env` files are loaded.

Keep this repository beside a checkout named `respan`, build its Anthropic instrumentation, then install the examples:

```sh
cd ../respan/javascript-sdks
# Install workspace dependencies following the SDK repository instructions first.
yarn workspace @respan/instrumentation-anthropic build
cd ../../respan-example-projects/typescript/tracing/anthropic
npm ci
npm run typecheck
npm run all
```

The target instrumentation is a local material copy (`install-links=true`), with released facade 2.5.0, tracing 1.6.1 and contract 1.3.4 companions.

| Script                           | Native coverage                                                                                                                                                            |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `01_basic.ts`                    | `APIPromise.withResponse()`, raw-only `asResponse()`, actual raw status, 76 messages/tools, image/document content, thinking, redacted thinking, citations and cache usage |
| `02_streaming.ts`                | Streamed thinking/signature/citations, fragmented tool arguments, early iterator return, controller abort and abort before the first `next()`                              |
| `03_tool_call.ts`                | Explicit tool execution with the actual model call ID, followed by a model response                                                                                        |
| `04_expected_error.ts`           | Canonical private model context and a controlled HTTP 429 error                                                                                                            |
| `05_parse_and_stream_helpers.ts` | Stable/beta native parse and stream helpers, parsed scalar values, beta compaction updates, unknown frames and native text callback                                        |
| `06_native_tool_runner.ts`       | Actual beta `toolRunner` agent loop and its real runnable tool; no aggregate LLM turn                                                                                      |
| `07_count_tokens_and_batches.ts` | Stable/beta token counting, native batch submission and actual JSONL success/error rows as common task work                                                                |
| `08_legacy_completion.ts`        | Native legacy text generation and streaming                                                                                                                                |

Set `RESPAN_EXAMPLE_RUN_ID` to label a bounded run. Set `RESPAN_EXAMPLE_CAPTURE=/absolute/path.jsonl` to save collector payloads, including exported trace/span/parent IDs. `RESPAN_EXAMPLE_COLLECTOR_URL` selects an existing collector. Internal naming hints must be removed by the released exporter before collection.

Hosted export is explicit: set `RESPAN_EXAMPLE_EXPORT=1` and supply `RESPAN_API_KEY`; optionally set `RESPAN_BASE_URL`. Real Anthropic requests are a separate opt-in: `RESPAN_ANTHROPIC_LIVE=1`, `ANTHROPIC_API_KEY`, and an explicit `RESPAN_ANTHROPIC_MODEL`. Credentials come only from the process environment. The local fixture's model name describes its SDK response shape; live availability depends on provider access and service support. Live mode skips fixture-only errors, asynchronous batch completion and legacy generation. Rich image/document/cache/thinking fixtures are limited to fixture mode; the live basic request uses one nonempty text message without fixture thinking or temperature controls.

Content privacy is checked on the actual model span. Workflow callbacks return only concise non-content summaries in private scenarios, because the released workflow decorator captures its callback result separately. Canonical HTTP status is verified before export; the current shared composite processor removes `http.*` attributes from OTLP, which remains a runtime follow-up.
