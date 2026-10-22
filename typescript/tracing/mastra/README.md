# Mastra tracing examples

Run released Mastra agents, tools, streams, workflows, native payload fidelity, and privacy scenarios through `@respan/instrumentation-mastra`.

```bash
cd typescript/tracing/mastra
npm ci
npm run typecheck
npm run examples
```

Node.js 22.13 or later is required. The target adapter is installed from the sibling `respan` checkout; build that package first. Other Respan packages come from their public releases. `.npmrc` copies the local package into `node_modules` during installation.

The default run uses Mastra's official deterministic model and an in-memory exporter. It needs no credentials and makes no provider or Respan requests.

- `example:basic`: native agent generation.
- `example:tool`: native agent tool execution with a JSON schema.
- `example:stream`: native agent streaming.
- `example:failure`: controlled native provider failure in a workflow.
- `example:workflow`: native workflow and step execution.
- `example:fidelity`: 80 messages, an 80-field tool schema, structured output, and a 5,003-dimensional embedding payload.
- `example:privacy`: a context-local content veto retained after the context exits.

To export the controlled scenarios, set `RESPAN_EXPORT=1` and provide `RESPAN_API_KEY`. `RESPAN_BASE_URL` optionally selects the Respan endpoint. Environment values may be loaded from the repository root `.env`. `RESPAN_EXAMPLE_RUN_ID` supplies a unique correlation marker; `MASTRA_CAPTURE_PATH` writes the converted local spans for scoped inspection. Credentials are never included in example output.

The example profile pins core 1.75.0 and observability 1.18.4. The adapter's native test suite also covers its declared core 1.36.0 / observability 1.13.0 minimum. Full schemas depend on the native events actually exposing `attributes.tools`; older SDK events may include names only. Mastra's serializer removes data before exporters run, so the fidelity fixture explicitly requests larger native serialization limits.
