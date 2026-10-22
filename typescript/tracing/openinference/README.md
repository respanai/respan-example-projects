# OpenInference TypeScript examples

Run real released OpenInference helpers and the official OpenAI instrumentor
through the local Respan adapter. Provider requests use native OpenAI methods
with deterministic HTTP/SSE fixtures. The default run sends traces to a local
loopback collector and needs no credentials.

```bash
cd typescript/tracing/openinference
npm ci
npm run typecheck
npm run all
```

The only local package is `@respan/instrumentation-openinference`, copied from
the sibling `respan` checkout by npm's `install-links=true`. Respan facade,
tracing and contract packages resolve to normal released npm dependencies.
Build the local instrumentation before installation.

| Script                       | Coverage                                                                                                                                            |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `01_native_helpers.ts`       | Agent/chain/tool nesting, context metadata/session/user/tags/prompt template and `observe` decorators.                                              |
| `02_full_llm_attributes.ts`  | Actual `getLLMAttributes` batches with 80 messages, 75 tools, request/response models, multimodal content, historical/current calls and zero usage. |
| `03_retrieval_embeddings.ts` | Native retrieval documents, complete 5001-dimensional vectors, model, zero score and null tool results.                                             |
| `04_native_openai.ts`        | Official upstream adapter, native APIPromise helpers, chat/SSE and controlled 400 errors.                                                           |
| `05_privacy.ts`              | Sticky late veto, canonical context veto and native OITracer redaction.                                                                             |
| `06_kinds_errors.ts`         | Reranker/guardrail/evaluator/prompt/decision kinds, false/zero/empty/null results and original thrown error identity.                               |

Run one scenario with `npm run 04:openai` (the other scripts have matching
numbered npm commands). `RESPAN_EXAMPLE_RUN_ID` selects an exact audit marker.
Set `RESPAN_EXAMPLE_CAPTURE_PATH` to save native IDs, parent IDs, attributes and
status after the released runtime's export preparation.

To send the same fixture traces to Respan, explicitly set
`RESPAN_EXAMPLE_EXPORT=1`, `RESPAN_API_KEY`, and optionally `RESPAN_BASE_URL`.
The examples do not load a dotenv file. `RESPAN_EXAMPLE_TRACE_CONTENT=false`
exercises the adapter's content ceiling across the suite. The pinned tracing
1.6.1 runtime still records user workflow inputs/results separately, including
when its `traceContent` option is false. OpenInference child spans obey the
adapter ceiling; parent-workflow capture remains a runtime follow-up.

Producer versions are pinned: OpenInference core 2.8.0, upstream OpenAI
instrumentation 4.4.1, OpenAI 7.32.0, OpenTelemetry trace SDK 2.10.0, Respan facade
2.5.0, tracing 1.6.1 and SDK 1.3.4. The adapter's separate minimum suite uses
OpenInference core 2.4.0; newer request/response-model attributes are available
only when that producer emits them.

OpenInference helpers serialize their own inputs before the native sampler.
The adapter controls its own post-sampler capture and the actual recording
span. It cannot recover attributes a producer discards before its setter
boundary. No attribute-limit environment override is needed for this suite.
