# Pi TypeScript tracing examples

These examples use the official Pi 1.1.0 session, extension runtime, provider parser, tools, compaction and branch APIs. A local HTTP SSE service supplies controlled provider responses. The instrumentation package is local; Respan companions come from npm.

Use Node 24. In sibling `respan` and `respan-example-projects` checkouts, build `respan/javascript-sdks/instrumentations/respan-instrumentation-pi`, then run from this directory:

```bash
npm ci
npm test
```

The checked-in lock uses `install-links=true` so npm copies the built target package and resolves its released companions in this example installation.

| Entry point               | Coverage                                                                                                      |
| ------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `01_sdk_stream.ts`        | Native subscription, streaming, usage, model and response IDs                                                 |
| `02_extension_tools.ts`   | Native extension, 75 messages, full schema, current/history tool IDs, 5001-value vector and structured result |
| `03_errors_abort.ts`      | Native provider errors and cancellation                                                                       |
| `04_compaction_branch.ts` | Manual compaction, branch summaries, resumed session trace scope                                              |
| `05_sessions_steering.ts` | A real tool boundary and native steering                                                                      |
| `06_capture_policy.ts`    | Canonical content veto with unchanged native output                                                           |
| `07_multiple_sessions.ts` | Independent session identities                                                                                |
| `08_live_provider.ts`     | Optional official OpenAI provider request                                                                     |

`run_all.ts` runs every entry point. The live case is skipped unless `RESPAN_PI_LIVE=1`, `OPENAI_API_KEY` and `PI_CHAT_MODEL` are set. The model must exist in Pi's official catalog.

Local checks emit no external traces. To export controlled traces, set `RESPAN_EXAMPLE_EXPORT=1`, `RESPAN_API_KEY`, `RESPAN_BASE_URL` and an exact `RESPAN_EXAMPLE_RUN_ID`. The SDK normalizes a trailing `/api` before appending `/api/v2/traces`. `RESPAN_EXAMPLE_TRACE_URL` can point to an OTLP collector. Inspect stored spans by the exact run marker and exported trace/span IDs; a successful export alone does not prove stored-body fidelity.

Before OTLP export, these examples apply the released Respan tracing package's public `transformReadableSpanBatch` helper in semantic mode. It assigns the shared display names and removes internal naming hints. The capture processor, sampling decisions, and native span/parent IDs remain unchanged. The examples pin tracing 1.6.1, which exports this helper from its public entrypoint.
