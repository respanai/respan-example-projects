# Cohere tracing examples

These examples exercise `respan-instrumentation-cohere` with Cohere chat, streaming chat, embeddings, and rerank.

## Environment

The scripts load `respan-example-projects/.env`.

Required:

- `RESPAN_API_KEY`

Optional:

- `RESPAN_BASE_URL`
- `CO_API_KEY` or `COHERE_API_KEY`
- `COHERE_CHAT_MODEL`
- `COHERE_EMBED_MODEL`
- `COHERE_RERANK_MODEL`
- `COHERE_USE_STUBS`
- `RESPAN_EXAMPLE_RUN_ID`

For this prerelease example update, install the edited instrumentation checkout and the requirements in one resolver operation from the examples repository root:

```bash
python -m pip install -r python/tracing/cohere/requirements.txt \
  -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-cohere
```

This installs Cohere 7.2 or later in the 7.x series with the paired adapter change and released Respan core packages. Use the edited adapter until its compatible package release is available. When no Cohere key is present, examples 01–03 use HTTPX transport fixtures with the released SDK’s request serialization, response models, and SSE parser. Set `COHERE_USE_STUBS=false` to call Cohere with your key. Examples 04–05 always use deterministic HTTP fixtures for tools, async multimodal embedding, rerank, provider errors, streaming disconnects, and early close. All examples export their spans to Respan; fixtures verify the SDK integration but do not establish live provider access.

## Run

```bash
python python/tracing/cohere/run_all_examples.py
```

Each script sets a stable workflow name:

- `cohere_chat.workflow`
- `cohere_streaming_chat.workflow`
- `cohere_embed_rerank.workflow`
- `cohere_async_tools_and_error.workflow`
- `cohere_async_streaming.workflow`

Set `RESPAN_EXAMPLE_RUN_ID` once when running the complete suite. Every trace carries `metadata.run_id` and `metadata.example_run_id` so platform inspection can be scoped to that exact run. The runner executes five scripts and stops on the first failed assertion.
