# LlamaIndex TypeScript tracing examples

These examples call released LlamaIndex clients against a local HTTP fixture by default. The Respan facade exports through its public pipeline to a local collector. No credentials are needed for the default run.

```bash
npm ci
npm run typecheck
npm run all
```

The instrumentation dependency points to the sibling `respan` checkout. Build that package before installation:

```bash
cd ../../../../respan/javascript-sdks
corepack yarn workspace @respan/instrumentation-llama-index build
cd ../../respan-example-projects/typescript/tracing/llama-index
npm ci
```

Only the target instrumentation is a local file dependency. The companion packages are released `@respan/respan` 2.5.0, `@respan/tracing` 1.6.1, and `@respan/respan-sdk` 1.3.4. `.npmrc` enables material installation of the file dependency. Examples use `llamaindex` 0.12.1 and current modular core 0.6.23/OpenAI 0.4.23; these have separate Settings objects, and the RAG example configures the meta Settings explicitly.

| Command                 | Native behavior                                                        |
| ----------------------- | ---------------------------------------------------------------------- |
| `npm run 01:basic`      | OpenAI chat and completion                                             |
| `npm run 02:rag`        | Document parsing, embedding, vector retrieval, synthesis, and query    |
| `npm run 03:tools`      | OpenAIAgent plus FunctionTool with actual tool call ID                 |
| `npm run 04:failure`    | Controlled provider HTTP 422 and native error propagation              |
| `npm run 05:stream`     | SSE through the native asynchronous iterator                           |
| `npm run 06:embedding`  | Two native embeddings with 5,001 coordinates each                      |
| `npm run 07:payloads`   | More than 75 messages/tools, historical call, multimodal input, schema |
| `npm run 08:privacy`    | Instrumentation input/output capture disabled                          |
| `npm run 09:concurrent` | Concurrent native chat and embedding calls                             |
| `npm run 10:responses`  | Native OpenAIResponses client                                          |

Set `RESPAN_CAPTURE_PATH=/absolute/path/capture.json` to save the local collector's OTLP JSON. This preserves native trace/span IDs, parents, and tool call IDs after the released exporter has processed spans.

Live provider calls and hosted export are independent, explicit options:

```bash
LLAMA_INDEX_LIVE=true OPENAI_API_KEY=... LLAMA_INDEX_MODEL=gpt-4o-mini npm run 01:basic
RESPAN_EXPORT=true RESPAN_API_KEY=... RESPAN_EXAMPLE_RUN_ID=my-unique-run npm run 03:tools
```

`OPENAI_BASE_URL` and `RESPAN_BASE_URL` can override those explicit destinations. Environment files are not loaded automatically. The failure example requires the controlled local provider. Live multimodal and structured output support depends on the selected model; the local fixture demonstrates native request handling and does not establish model compatibility.

Embedding token usage is omitted because the native LlamaIndex method returns vectors without the provider usage object. Generic provider callbacks remain supported; standalone callback-only provider rejections that emit no terminal event have no native completion to export. Hosted stored-trace acceptance is a separate verification gate.
