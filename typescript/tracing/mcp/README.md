# MCP + Respan Examples (TypeScript)

Eight native SDK scenarios run through released `@respan/respan` 2.5.0,
`@respan/tracing` 1.6.1 and `@respan/respan-sdk` 1.3.4. They use genuine
connected MCP clients, servers and `InMemoryTransport`, with v1.32.1 and the
stable split v2.3.1 packages. No provider account is required.

Use Node.js 20 or later. Place this repository beside the `respan` SDK checkout
and build its `@respan/instrumentation-mcp` package first. The relative `file:`
dependency installs a material copy of that package; the companion Respan
packages come from npm.

```bash
cd typescript/tracing/mcp
npm ci
npm run typecheck
npm run all
```

By default each script starts a local HTTP collector and points the normal
Respan exporter at it. The scripts verify native results, flush and shut down
the public runtime, check exported span names and print native trace IDs.
They do not load a repository `.env` file. Set `RESPAN_EXAMPLE_CAPTURE_PATH`
to save the local OTLP JSON payloads for inspection.

| Script                        | Native coverage                                                                                  |
| ----------------------------- | ------------------------------------------------------------------------------------------------ |
| `01_client_tool_call.ts`      | Tools, structured output and falsy values                                                        |
| `02_resources_and_prompts.ts` | Resource list/read/templates and prompt list/get                                                 |
| `03_legacy_tool_api.ts`       | v1 high-level legacy `McpServer.tool()`                                                          |
| `04_protocol_callbacks.ts`    | Sampling, elicitation, roots and logging notifications                                           |
| `05_split_v2.ts`              | Stable v2 `Client`, `McpServer` and transport                                                    |
| `06_experimental_tasks.ts`    | v1 task stream, status, result, list and cancel                                                  |
| `07_full_content.ts`          | 80 tool definitions/messages, 5,001 values, multimodal content, 50K text, `_meta` and pagination |
| `08_privacy_and_errors.ts`    | Canonical context privacy veto, native rejection and cancellation                                |

Sampling callbacks are controlled client responses to actual MCP protocol
requests. They are recorded as protocol task spans; no provider usage or LLM
execution is inferred. Native protocol request IDs are distinct from model
tool-call IDs. v1.0.0 lacks high-level `McpServer`, elicitation and experimental
tasks; the stable v2 SDK does not expose v1 experimental tasks.

To explicitly export a controlled run to Respan, provide credentials in the
shell and opt in. `RESPAN_EXAMPLE_RUN_ID` gives the run an exact lookup marker.

```bash
RESPAN_EXPORT=true RESPAN_EXAMPLE_RUN_ID=mcp-controlled-run npm run all
```

`RESPAN_API_KEY` is required only for explicit export. `RESPAN_BASE_URL` may
override the export destination. Hosted trace acceptance requires inspection
of that actual run after export; the local collector verifies the runtime
pipeline and does not establish hosted acceptance.
