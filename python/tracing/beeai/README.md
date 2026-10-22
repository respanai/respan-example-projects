# BeeAI tracing examples

These nine scenarios exercise released BeeAI APIs with a controlled model
boundary: RequirementAgent, chat, a tool, an expected error, Run event streaming,
embeddings, model tool calls and tool results, Workflow with structured output,
and content privacy changes during a run.

```bash
pip install respan-ai respan-instrumentation-beeai beeai-framework python-dotenv
python python/tracing/beeai/run_all.py
```

The default `BEEAI_EXAMPLE_MODE=fixture` runs locally without provider requests or
trace export. The SDK's real agents, workflows, tools, event stream, validation,
and exception handling still run. Fixture usage and vectors are explicitly
controlled values, not measurements of a live provider.

To export those synthetic scenarios, set `RESPAN_EXAMPLE_EXPORT=1` and
`RESPAN_API_KEY`. `RESPAN_EXAMPLE_RUN_ID` assigns one exact marker to the complete
suite. Export mode reads the repository `.env` with `override=False`;
`RESPAN_EXAMPLE_ENV_FILE` selects another environment file. The default destination
is `https://api.respan.ai/api/v2/traces`. Use `RESPAN_BASE_URL` only to select an
intended alternative API base.

`BEEAI_EXAMPLE_MODE=live` selects BeeAI's provider adapters and requires the
provider's own credentials and model access. `BEEAI_MODEL` defaults to
`openai:gpt-4.1-nano`. Live mode does not export unless
`RESPAN_EXAMPLE_EXPORT=1` is also set. It does not rewrite provider credentials or
provider endpoints. The streaming, tool-call, structured-output and agent cases
require a model that supports those features; model behavior and access can fail
independently of instrumentation. The error scenario uses a nonexistent model in
live mode. Embedding live mode uses `openai:text-embedding-3-small`.

The fixtures run on BeeAI 0.1.51 and 0.1.85. The minimum release lacks newer cache
usage fields, which the adapter omits. Provider adapters and serving/ACP/A2A,
external MCP tools, evaluator transports, and provider-specific multimodal
support are not exercised by these controlled examples.
