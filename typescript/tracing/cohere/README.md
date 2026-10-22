# Cohere TypeScript tracing

Nine examples use `cohere-ai` 8.1.0 with the local `@respan/instrumentation-cohere` package and released Respan companions. Build the instrumentation in the sibling `respan` checkout before installing:

```bash
cd ../../../../respan/javascript-sdks
corepack yarn workspace @respan/instrumentation-cohere build
cd ../../../respan-example-projects/typescript/tracing/cohere
npm ci
npm run typecheck
npm run examples
```

The default run calls a local Cohere HTTP/SSE fixture and sends spans through the released Respan exporter to a local HTTP collector. It needs no credentials and prints exported span IDs and parent IDs. `RESPAN_LOCAL_CAPTURE_FILE=/absolute/path.jsonl` saves the local collector payloads; `RESPAN_COLLECTOR_URL` overrides the collector destination for controlled validation.

The scenarios cover 80 messages and tool definitions with multimodal content, streamed tool argument fragments, five embedding types with a 5,001-entry float vector, rerank documents and zero relevance scores, all legacy generations, expected HTTP errors, disabled content capture, v1 chat and streaming, and v2 document parsing. Parsing creates a tool span with its actual document result; rerank search units are not token counts.

Hosted export and real provider calls are separate opt-ins. Set `RESPAN_EXPORT=true` and `RESPAN_API_KEY` to send traces to Respan; optionally set `RESPAN_BASE_URL`. Set `COHERE_USE_REAL_API=true` and `COHERE_API_KEY` to call Cohere. Only these opt-ins load the repository-root `.env`. Real provider availability and model access may differ from the local fixtures; replace the fixture document/image URLs with accessible URLs for live requests.

The instrumentation supports v1 APIs starting at 7.7.5; that version does not expose v2 clients or document parsing. These current-SDK examples require 8.1.0. The package's native regression suite separately validates exact minimum and current SDK versions.
