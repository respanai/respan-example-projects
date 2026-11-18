# Vertex AI tracing examples

Run the released Vertex SDK through real Google clients and protobuf parsing over a local gRPC server. The fixture uses anonymous credentials and verifies that each native client selects its loopback transport. No deployed Vertex service is required for the default run.

```bash
pip install .
python run_all.py
```

The runner covers all numbered scripts:

| Script | Native behavior |
| --- | --- |
| `01_generate_content.py` | Sync generation, native config and media part |
| `02_chat_streaming.py` | Chat, 70 chunks, consumed and unread close |
| `03_tool_execution.py` | Full tool schema, function call/response, history and connected Respan tool span |
| `04_async_generate.py` | Async generation/chat/stream and early/unread aclose |
| `05_expected_error.py` | Real Google `ServiceUnavailable` from local gRPC status |
| `06_live_provider.py` | Optional live Google call; skipped by default |
| `07_embeddings.py` | Sync/async embeddings with complete 5,001-element vectors |
| `08_privacy.py` | Initial denial and irreversible late stream denial |

Default runs record spans in memory. To send the controlled traces to Respan, set `RESPAN_EXAMPLE_EXPORT=1` and configure `RESPAN_API_KEY` in the repository `.env` or environment. The exporter endpoint is `https://api.respan.ai/api/v2/traces`. Set `RESPAN_EXAMPLE_RUN_ID` for a repeatable marker and optionally `RESPAN_EXAMPLE_REPORT_DIR` to save local span bodies. Reports contain the controlled example payloads.

A live call requires `VERTEXAI_EXAMPLE_LIVE=1`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` and application default credentials. `VERTEXAI_MODEL` optionally selects the model. Live calls may incur provider charges; they are separate from trace export. The controlled audit does not run this option.

Google's [migration notice](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/deprecations/genai-vertexai-sdk) deprecates the Vertex generative modules. They remain executable in audited `google-cloud-aiplatform==2.3.0`; the examples cover APIs actually present, with exact minimum `1.71.0` checked separately. These examples do not exercise the `google-genai` SDK.

The instrumentor returns stream protocol proxies: concrete generator type and stream object identity change, while original chunks, iteration and explicit close/aclose delegate to the native generator. Unary values and errors remain native. No tokens or success HTTP status are invented; partial/unread streams retain only actual consumed response data. Privacy denial preserves the native result and clears captured content/diagnostics.
