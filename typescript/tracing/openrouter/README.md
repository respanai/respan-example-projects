# OpenRouter TypeScript examples

These examples use the real official OpenRouter client and native response parsers. By default, a controlled HTTP transport supplies reproducible responses and an in-memory OTel exporter captures the resulting spans. Provider credentials are optional for this mode.

```bash
npm ci
npm run typecheck
npm run examples
```

The local `@respan/instrumentation-openrouter` dependency uses the adjacent `respan` checkout. Build that leaf before installing these examples:

```bash
cd ../../../../respan/javascript-sdks/instrumentations/respan-instrumentation-openrouter
npm run build
```

All other packages resolve from npm. `.npmrc` enables normal file-package installation so the vendor SDK and OTel module instances come from this example's dependency tree.

| Script               | Coverage                                                                                                                  |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `npm run chat`       | Native chat, requested/resolved model, zero token counts                                                                  |
| `npm run tools`      | Request schema and current tool-call payload                                                                              |
| `npm run stream`     | Native EventStream text and terminal usage                                                                                |
| `npm run embeddings` | Two complete 5001-element vectors                                                                                         |
| `npm run responses`  | Public Responses endpoint (BetaResponses on the SDK minimum)                                                              |
| `npm run call-model` | Lazy SDK ModelResult, cached promise, native tool callback and continuation                                               |
| `npm run outcomes`   | Standalone APIPromise inspection, 75-message history, controlled HTTP error, cancellation, content denial and suppression |

`npm run examples` executes all seven entrypoints. Fixture mode expects 11 model/embedding spans and seven workflow spans. It asserts that the native child spans have workflow parents. Each run prints its `RESPAN_EXAMPLE_RUN_ID` marker.

To export the same controlled traces to Respan, set `RESPAN_API_KEY` and `RESPAN_EXPORT_TRACES=1`. `RESPAN_BASE_URL` is optional. The exporter normalizes a trailing `/api` before appending `/api/v2/traces`. A successful local run confirms local behavior; exported bodies and platform records require separate inspection.

```bash
RESPAN_EXPORT_TRACES=1 RESPAN_EXAMPLE_RUN_ID=openrouter-controlled-run npm run examples
```

Live provider calls require `RESPAN_LIVE_OPENROUTER=1`, `OPENROUTER_API_KEY`, `OPENROUTER_CHAT_MODEL`, and `OPENROUTER_EMBEDDING_MODEL`. They use the OpenRouter provider directly. Controlled error/privacy/large-payload scenarios are skipped in live mode and the summary reports those skips. Respan trace-export credentials do not substitute for OpenRouter provider credentials.

The package supports `@openrouter/sdk` 0.13.7 and later and is validated against 1.4.25. SDK `callModel` remains available in 1.4.25; the separate `@openrouter/agent` package is outside these examples. The examples use published Respan companions and an explicit public OTel 2 provider with unlimited local attribute count/value lengths so large fixture payloads can be checked in full.
