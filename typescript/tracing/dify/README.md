# Dify TypeScript tracing examples

These examples exercise `@respan/instrumentation-dify` with the official
`dify-client` 3.1.0 package. By default they start a deterministic loopback
Dify Service API, so only `RESPAN_API_KEY` is required. Set `DIFY_BASE_URL` and
the matching Dify keys to use real apps instead.

## Install and run

```bash
npm install --install-links=false
npm run typecheck
RESPAN_EXAMPLE_RUN_ID=dify-ts-audit-001 npm run examples
```

When the marker is omitted, `run_all.ts` generates and prints one shared
`RESPAN_EXAMPLE_RUN_ID` and passes it to all five child scenarios.
For local validation that must not export traces, set
`RESPAN_EXAMPLE_NO_EXPORT=true`; this permits an empty `RESPAN_API_KEY` while
retaining the instrumentation pipeline and routes the exporter to a
discard-only loopback sink.

The five scenarios cover:

- blocking chat with model and token usage;
- SSE chat, with span completion after full AsyncIterable consumption;
- text completion and workflow execution;
- Knowledge Base listing, Workspace models, and a RAG pipeline;
- multipart file upload and a controlled HTTP error.

Live RAG execution is optional and requires `DIFY_RAG_DATASET_ID` and
`DIFY_RAG_START_NODE_ID`; the loopback suite always exercises it. Each script
prints the exact `RESPAN_EXAMPLE_RUN_ID` marker and has one parent workflow.
After a full run, verify five scoped trace trees plus child Dify spans on the
Respan platform. Check parent links, log types, endpoint metadata, input/output,
model and usage on chat/text spans, workflow/RAG outputs, the controlled error,
and absence of duplicate spans or off-contract aliases.
