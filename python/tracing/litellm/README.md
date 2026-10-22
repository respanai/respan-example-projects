# LiteLLM Respan examples

The default `RESPAN_LITELLM_MODE=fixture` runs actual LiteLLM and OpenAI SDK calls
against controlled HTTP transports. It does not contact a model provider.
Trace export uses `RESPAN_API_KEY` (or `RESPAN_GATEWAY_API_KEY`) and
`RESPAN_BASE_URL` from the repository root `.env`. Existing environment values
are preserved. Each complete runner invocation uses one marker in trace groups
and metadata.

```bash
pip install -r python/tracing/litellm/requirements.txt
python python/tracing/litellm/run_all_examples.py
```

| Script | Coverage |
| --- | --- |
| 01 | Native completion and actual provider usage |
| 02 | Streaming, source usage and caller context |
| 03 | Respan attribution |
| 04 | Current native tool calls |
| 05 | Controlled native provider failure |
| 06 | Async completion |
| 07 | Async streaming |
| 08 | 100-property tool schema, historical/current IDs and 5,000-value provider/tool vectors |
| 09 | Public Responses sync/async and both streaming paths |
| 10 | Delayed parent veto, zero/absent usage and native private-source flags |
| 11 | 150-message/choice arrays and complete sensitive-named schema properties with credential values redacted |

Scripts 08–11 are controlled fixtures only. The minimum LiteLLM 1.80.10 Responses
helper requires upstream optional FastAPI/orjson, included in requirements.
Its stream wrapper lacks `aclose`; that native API is tested on current 1.104.0
and explicitly skipped on the minimum.

For real gateway calls in scripts 01–07, set `RESPAN_LITELLM_MODE=live`,
`RESPAN_GATEWAY_API_KEY`, `RESPAN_GATEWAY_BASE_URL`, and
`RESPAN_LITELLM_MODEL` (or `RESPAN_MODEL`). This optional mode may incur provider
charges and is not part of controlled validation. The invalid-key error example
still intentionally fails. Scripts 08–11 explicitly skip in live mode. The
fixtures do not validate live gateway/provider credentials, LiteLLM proxy/router
or unrelated audio/image/rerank APIs.

Exact OpenTelemetry 1.38 minimum validation uses FastAPI 0.115.12; current
FastAPI 0.142.2 requires OpenTelemetry API 1.44 or newer.
