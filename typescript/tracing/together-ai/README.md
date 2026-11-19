# Together AI native SDK tracing examples

Run the actual `together-ai` 0.58.0 client through Respan. The default mode uses
controlled fetch/SSE responses and a local trace collector. It needs no
provider or Respan credentials and never infers a provider call from a fake
client. The SDK owns request encoding, APIPromise helpers and stream parsing.

Keep `respan` and `respan-example-projects` as sibling checkouts. Build the
Together instrumentation first, then run:

```bash
npm ci
npm run typecheck
npm run examples
```

`.npmrc` installs only the local instrumentation as a material copy. Respan
facade 2.5.0, tracing 1.6.1 and SDK 1.3.4 come from npm. Reinstall after rebuilding
the local instrumentation. Node20.12 or newer is required.

| Script                                  | Native feature coverage                                                                                  |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `01_chat_completion.ts`                 | Multimodal chat, separate answer/reasoning fields, actual usage                                          |
| `02_chat_streaming.ts`                  | Multiple choices, native controller, full stream and early return                                        |
| `03_tool_calls.ts`                      | Native tool call ID, actual application callback, subsequent native history; no fabricated fallback call |
| `04_text_completion_embedding.ts`       | Text completion and a full 5001-element embedding                                                        |
| `05_image_rerank.ts`                    | Image generation and actual returned rerank document                                                     |
| `06_audio_transcription_translation.ts` | Native binary speech response and actual upload API paths                                                |
| `07_expected_error.ts`                  | Controlled native429 rejection                                                                           |
| `08_content_opt_out.ts`                 | Plugin/runtime/environment opt-out with actual requests still executed                                   |
| `09_current_features.ts`                | Full 80 messages/80 tools, response helpers, raw unread HTTP response                                    |

Each script runs in a separate process. Set `RESPAN_EXAMPLE_CAPTURE_PATH` to
save actual public-runtime span IDs, parent links, attributes and local OTLP
requests; use a separate path per script.

Exporting those controlled traces is a separate mode:

```bash
RESPAN_EXAMPLE_EXPORT=1 RESPAN_API_KEY="$RESPAN_API_KEY" \
  RESPAN_EXAMPLE_RUN_ID="together-audit" npm run examples
```

`RESPAN_BASE_URL` selects the configured trace destination. Provider traffic
still uses the local fetch fixture. Export and live inference flags are
independent. Set `TOGETHER_EXAMPLE_LIVE=1`, `TOGETHER_API_KEY`, and actual model
overrides (`TOGETHER_CHAT_MODEL`, `TOGETHER_COMPLETION_MODEL`,
`TOGETHER_EMBEDDING_MODEL`, `TOGETHER_IMAGE_MODEL`, `TOGETHER_RERANK_MODEL`,
`TOGETHER_SPEECH_MODEL`) only for explicit live runs; native fixture assertions
are disabled for live responses. The controlled-error case still requires a
rejected model request. No Gateway support is implied by a custom base URL.

Binary speech and `asResponse` bodies stay unread by the adapter. The SDK's
native request serialization remains necessary under content opt-out. The
privacy script sets `RESPAN_TRACE_CONTENT=false` for its workflow decorator in
addition to plugin/runtime options. Historical messages never create tool
execution spans; only the callback actually invoked in script 03 does.
