# Vertex AI native SDK tracing examples

Use current `@google/genai` 2.28.0 with `vertexai:true`, while retaining explicit
legacy `@google-cloud/vertexai` 1.12.0 examples. Google [retires the legacy
SDK after June 24, 2026](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/deprecations/genai-vertexai-sdk)
and recommends the Google GenAI SDK. These tests establish SDK compatibility;
they do not extend Google's support period or establish live model access.

Default mode runs the real released clients against controlled HTTP/SSE fetch
transports and a local trace collector. It requires no Google or Respan
credentials. The synthetic `FakeVertexAI` producer has been removed.

Keep `respan` and `respan-example-projects` as sibling checkouts and build the
Vertex instrumentation first:

```bash
npm ci
npm run typecheck
npm run examples
```

Node20.12 or newer is required. `.npmrc` materializes only the local target;
the facade 2.5.0, tracing 1.6.1 and contract SDK 1.3.4 resolve from npm. Reinstall
when the local target is rebuilt.

| Script                           | Actual native coverage                                                                                          |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `01_generate_content.ts`         | Current multimodal generation, system instructions, reasoning/signatures, returned image parts and actual usage |
| `02_generate_content_stream.ts`  | Native generators and SSE parsing, full consumption and early return                                            |
| `03_chat_tool_call.ts`           | Native chat history and actual function call/result IDs                                                         |
| `04_error_capture.ts`            | Controlled native429 rejection                                                                                  |
| `05_automatic_function_calls.ts` | Native AFC loop, actual callback decorated with its returned call ID, two real model requests                   |
| `06_embeddings.ts`               | Actual native embedding response with 5001 values                                                               |
| `07_image_video.ts`              | Image inference and a pending video-start operation; no fictional completed video                               |
| `08_content_opt_out.ts`          | Actual operation with plugin/runtime/environment content denied                                                 |
| `09_legacy_vertex.ts`            | Retained legacy GA, preview, chat and streamed chat APIs                                                        |
| `10_current_features.ts`         | Full 80 message history and80 tool declarations under the default OTel budget                                   |
| `11_image_inference.ts`          | Native image editing, upscaling, recontext and segmentation                                                     |

Each script runs separately. `RESPAN_EXAMPLE_CAPTURE_PATH` saves the actual
public-runtime span IDs, parent links, attributes and local OTLP requests.
Use separate paths when running multiple scripts.

To export these same controlled traces:

```bash
RESPAN_EXAMPLE_EXPORT=1 RESPAN_API_KEY="$RESPAN_API_KEY" \
  RESPAN_EXAMPLE_RUN_ID="vertex-audit" npm run examples
```

`RESPAN_BASE_URL` selects the configured trace destination; Google traffic
remains controlled. Live inference is independently opt-in with
`VERTEXAI_EXAMPLE_LIVE=1`, `GOOGLE_CLOUD_PROJECT`,
`GOOGLE_CLOUD_LOCATION`, Google Application Default Credentials and actual
`VERTEXAI_MODEL`/`VERTEXAI_EMBEDDING_MODEL` overrides. Image/video examples
also require the corresponding provider models to be available. Native
fixture assertions are disabled in live mode. The custom endpoint capability
does not establish Respan Gateway support.

This leaf instruments Vertex-backed inference only. Gemini Developer API,
administrative/cache/batch/file/tuning APIs, token counting, operation polling,
Live WebSockets and Interactions are out of scope. Native SDK preprocessing
and required request serialization still occur under content opt-out. The
privacy script sets `RESPAN_TRACE_CONTENT=false` for the separate public
workflow decorator as well as plugin/runtime options.
