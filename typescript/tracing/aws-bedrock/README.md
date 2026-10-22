# AWS Bedrock TypeScript tracing examples

These examples call the released AWS `BedrockRuntimeClient.send` with native
commands. The default fixture transport runs AWS serialization, deserialization,
and binary eventstream decoding locally. It needs no AWS or Respan credentials.

Keep the `respan` and `respan-example-projects` repositories beside one another.
Build the Bedrock instrumentation package in `respan`, then run:

```bash
cd typescript/tracing/aws-bedrock
npm ci
npm run typecheck
npm run examples
```

The instrumentation dependency uses a relative local package; `.npmrc` copies
that package during installation. The facade, tracing runtime, and contract SDK
resolve to published versions. Rebuild the instrumentation and run `npm ci`
after changing it.

| Script                  | Native coverage                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------- |
| `01_converse.ts`        | Messages, system prompt, tool definitions, output, tool calls, usage                              |
| `02_invoke_model.ts`    | Anthropic-style InvokeModel request and byte response                                             |
| `03_streaming.ts`       | Both AWS eventstream APIs, fragmented tool input, streamed text                                   |
| `04_expected_error.ts`  | Controlled 429 service error through AWS deserialization                                          |
| `05_native_features.ts` | 76 messages and tools, callback overload, early stream return, 5001-dimensional fixture embedding |

The default local exporter captures real span and parent IDs in memory. To save
those records, set `RESPAN_EXAMPLE_CAPTURE` to a path containing `{pid}` because
the runner starts each script in its own process:

```bash
RESPAN_EXAMPLE_RUN_ID=bedrock-local-check \
RESPAN_EXAMPLE_CAPTURE='/tmp/bedrock-{pid}.json' npm run examples
```

Set `RESPAN_EXAMPLE_EXPORT=1` with `RESPAN_API_KEY` to export through the Respan
runtime. `RESPAN_BASE_URL` optionally selects a collector or configured Respan
destination. Credentials are read only for an explicitly enabled export. Use
`AWS_BEDROCK_TRACE_CONTENT=false` to exercise content denial.

```bash
RESPAN_EXAMPLE_RUN_ID=bedrock-export-check \
RESPAN_EXAMPLE_EXPORT=1 npm run examples
```

Set `AWS_BEDROCK_EXAMPLE_MODE=live` to use AWS instead of fixture transport.
Configure the normal AWS credentials chain and `AWS_REGION`; optionally set
`AWS_BEDROCK_MODEL_ID` and `AWS_BEDROCK_INVOKE_MODEL_ID`. Live calls require model
access and incur provider usage. The deterministic error and vector are fixture
scenarios; live providers choose their own response and error behavior.

The examples pin AWS SDK `3.1149.0`. The instrumentation suite also tests
`3.704.0`, the first published version satisfying its `>=3.700.0` peer range;
there is no published `3.700.0` Bedrock package. Features added after `3.704.0`
require a newer AWS serializer, including audio, extended cache TTL, structured
output configuration, and system tools. Unsupported commands such as guardrails,
token counting, async inference, and bidirectional inference pass through.
