# Azure OpenAI TypeScript examples

These examples call the real `openai` **7.32.0** `AzureOpenAI` client. By default,
a controlled HTTP/SSE transport supplies provider responses and a local OTLP
collector receives spans through the released Respan exporter. No credentials
are needed. SDK methods are never replaced with fake client methods.

Keep this repository beside a checkout named `respan`, build its Azure
instrumentation package, then install the examples:

```sh
cd ../respan/javascript-sdks
# Install the workspace dependencies first, following the SDK repository instructions.
yarn workspace @respan/instrumentation-azure-openai build
cd ../../respan-example-projects/typescript/tracing/azure-openai
npm ci
npm run typecheck
npm run all
```

The target instrumentation is installed from the adjacent SDK checkout; Respan
2.5.0, tracing 1.6.1 and SDK 1.3.4 are released companions. `.npmrc` uses
`install-links=true`, so `npm ci` installs the built target as a material copy.

| Script                       | Native coverage                                                                                                |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `01_chat_completion.ts`      | 76-message/tool chat completion, complete canonical output under the default attribute budget, workflow parent |
| `02_streaming_tool_calls.ts` | Streamed function call, explicit tool execution with its actual call ID, final answer                          |
| `03_text_completion.ts`      | Text completion input/output                                                                                   |
| `04_embeddings.ts`           | Embedding inputs, full 5001-element fixture vector and zero vector                                             |
| `05_responses.ts`            | Responses parsing and native streaming helper                                                                  |
| `06_privacy_and_errors.ts`   | Private model span and controlled HTTP 429 error                                                               |

Each script prints its workflow name and exact run ID. Set
`RESPAN_EXAMPLE_RUN_ID` to correlate a bounded run. Set
`RESPAN_EXAMPLE_CAPTURE=/absolute/path/otlp.jsonl` to save locally received OTLP
payloads, including native trace/span/parent IDs. An existing local collector can
be selected with `RESPAN_EXAMPLE_COLLECTOR_URL`.

To export fixture traces to Respan, set `RESPAN_EXAMPLE_EXPORT=1` and
`RESPAN_API_KEY`; optionally set `RESPAN_BASE_URL`. The examples read environment
variables already supplied to the process and do not load `.env` files.

To make real Azure requests, also set `RESPAN_AZURE_LIVE=1`,
`AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, and `OPENAI_API_VERSION`.
Use deployments that support each chosen operation. Responses can use
`AZURE_OPENAI_RESPONSES_DEPLOYMENT`. The live privacy example skips its
fixture-only HTTP error. Azure service availability is separate from SDK method
availability.

The instrumentation additionally tests `openai` 4.47.2 and legacy
`@azure/openai` 1.0.0-beta.1/1.0.0-beta.12 through native transports. The stable
`@azure/openai` 2.0.0 package supplies Azure-specific types; it does not export
the legacy client.
