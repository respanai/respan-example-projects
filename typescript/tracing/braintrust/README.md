# Braintrust TypeScript tracing examples

Run actual Braintrust logger/span/traced APIs and `wrapOpenAI` with a real OpenAI
client over controlled loopback HTTP/SSE. The default run uses fixture keys and
sends Respan OTLP through the released public runtime to the same local service.
It needs no account credentials and makes no hosted Braintrust/provider requests.

```bash
npm ci
npm run typecheck
npm run examples
```

The local target is a material copy installed from the relative `file:` dependency;
`.npmrc` enables ordinary npm directory installs. Respan facade 2.5.0, tracing
1.6.1 and SDK 1.3.4 are released companions. Braintrust is pinned to 3.37.2; the
adapter is also tested at its exact declared minimum, 3.9.0.

- `01_llm_chat.ts`: 80 multimodal messages, 82 tools, actual response tool-call
  ID, explicit total usage, and native SSE iteration/controller behavior.
- `02_task_and_tool.ts`: native agent/task/tool parentage, tool call correlation,
  a 5001-element vector logged through the native API, and false/zero/empty/null
  input/output cases.
- `03_merge_and_error.ts`: partial flush and native merge updates, original
  application/provider errors, scoring, and an immutable content-denial context.

Set `RESPAN_EXAMPLE_RUN_ID` to correlate a run. `RESPAN_EXAMPLE_CAPTURE=/absolute/path.json`
retains the actual locally received OTLP spans for inspection. To explicitly
export controlled examples to Respan, set `RESPAN_EXAMPLE_EXPORT=1`, supply
`RESPAN_API_KEY` in the process environment, and optionally set `RESPAN_BASE_URL`.
The scripts never load credential files. The Braintrust and provider transports
remain loopback fixtures in export mode.

Braintrust's provider wrapper logs embedding length rather than full vectors;
the vector scenario demonstrates the native API that exposes complete values.
Native spans without an end marker stay unfinished. Complete canonical JSON is
preserved even when OTel's default 128-attribute budget limits optional indexed
message attributes. Hosted previews may apply independent display limits.
