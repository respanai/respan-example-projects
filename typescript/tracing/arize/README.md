# Arize Phoenix + Respan TypeScript examples

Run the released Phoenix 2.2.0 helper APIs with the Arize adapter. Native
embedding builders take `vector`; the retrieval/embedding scenario uses that
released schema. The default run uses a local loopback collector and needs no
credentials.

```bash
cd typescript/tracing/arize
npm ci
npm run typecheck
npm run all
```

Build the sibling local Arize instrumentation before installation. It is the
only `file:` dependency and npm copies its package material with
`install-links=true`. OpenInference 1.2.1, Respan facade 2.5.0, tracing 1.6.1 and
SDK 1.3.4 are released companions.

| Script                                | Native coverage                                                  |
| ------------------------------------- | ---------------------------------------------------------------- |
| `01_trace_helpers.ts`                 | `traceAgent`, `traceChain`, `traceTool` and context propagation. |
| `02_manual_llm_attributes.ts`         | `withSpan` and actual LLM attribute builders.                    |
| `03_retrieval_embedding_redaction.ts` | Retrieval, correct embedding-vector API and OITracer redaction.  |
| `04_observe_decorator.ts`             | Standard `observe` decorators.                                   |

`RESPAN_EXAMPLE_RUN_ID` sets an exact marker. `RESPAN_EXAMPLE_CAPTURE_PATH`
appends JSONL span snapshots with native IDs and parents. Export to Respan is
explicit: set `RESPAN_EXAMPLE_EXPORT=1`, `RESPAN_API_KEY`, and optionally
`RESPAN_BASE_URL`. These scripts do not load dotenv files.

The Arize adapter consumes released OpenInference 1.2.1. That companion does
not yet map native embedding vectors/model or indexed tool definitions to the
complete canonical contract, and its bridge does not enforce Respan's content
ceiling. These downstream mapping/privacy gates remain partial until a fixed
OpenInference companion is released. Native OITracer redaction still applies.
The examples do not substitute an unpublished local OpenInference package.
