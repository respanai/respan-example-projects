# Native Hugging Face Transformers examples

These examples run an actual tiny random GPT-2 CPU model with a local WordLevel tokenizer. They download no model weights and call no hosted inference provider. They demonstrate native `TextGenerationPipeline` behavior and Respan instrumentation; the generated words are not useful model answers.

```bash
pip install -r requirements.txt
python run_all.py
```

Local recording is the default. The released `respan-ai==4.1.0` facade is compatible with this checkout package version; a newer facade may require a newer published instrumentation version. For checkout validation, install this target package rather than substituting its PyPI release.

| Script | Native behavior |
| --- | --- |
| `01_text_generation_pipeline.py` | String, keyword input, and native GenerationConfig |
| `02_batch_prompts.py` | Nested batches and multiple candidates |
| `03_trace_content_disabled.py` | Canonical/legacy context flags and late iterator veto |
| `04_real_tiny_pipeline.py` | Token IDs, a 5000-token native input/result, empty text, and current native scores |
| `05_chat_and_tools.py` | 75-message history and native tool schema |
| `06_lazy_iterators.py` | Exact native iterator and two pending siblings |
| `07_native_streamer.py` | Native TextIteratorStreamer callback with explicit thread context |
| `08_native_errors.py` | Genuine native generation argument errors, captured and private |

All scripts run on the supported Transformers 4.45.0 floor. That release has no native pipeline `tools` or additional ModelOutput result options, so the chat example records an explicit tool-feature skip and still runs native chat generation. Current Transformers exposes `tools`; the schema includes credential defaults to verify redaction. Lazy inputs are consumed only by the native SDK; some SDK releases themselves peek the first generator value.

Exporting controlled synthetic traces is explicit:

```bash
RESPAN_EXAMPLE_EXPORT=1 \
RESPAN_EXAMPLE_RUN_ID=your-fresh-run-id \
RESPAN_EXAMPLE_ENV_FILE=/absolute/path/to/.env \
RESPAN_EXAMPLE_OUTPUT_DIR=/absolute/path/to/evidence \
python run_all.py
```

Only export mode loads `.env`. Set `RESPAN_API_KEY` (or `RESPAN_GATEWAY_API_KEY`). Evidence contains local spans and the actual released exporter's HTTP request bodies and response statuses. HTTP 200 is transport acceptance; stored tree and detail inspection is a separate semantic gate. This suite has no live-provider or deployment path; hosted inference and remote model downloads require a separate explicitly configured application.
