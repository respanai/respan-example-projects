# LlamaIndex tracing examples

The default suite runs released LlamaIndex core, Workflows, OpenAI LLM, and
OpenAI embedding code against controlled HTTP responses. It needs no credentials
and sends no model requests or traces to a service.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
RESPAN_EXAMPLE_RUN_ID=llama-index-check python run_all.py
```

The twelve scripts cover completion, chat, a full 3072-dimensional embedding,
a query engine, ReAct tools, function-calling tools, synchronous and asynchronous
streaming, a standalone workflow, structured prediction, private content,
controlled provider failure, and sparse embeddings. Dense embedding counts come
from the controlled provider response. The sparse model uses the SDK's released
base class with known vectors and reports no invented token usage.

`run_all.py` continues after failed or timed-out children and reports an aggregate
exit status. Each initialized Respan instance flushes and shuts down in `finally`.
The shell's `RESPAN_EXAMPLE_RUN_ID` wins over `.env` values; all environment files
load with `override=False`.

To export controlled fixture traces, set `RESPAN_LLAMA_INDEX_EXPORT=1` and
`RESPAN_API_KEY`. The default endpoint is `https://api.respan.ai/api`. Model
requests still use the HTTP fixtures.

For live Gateway validation of examples 01–10, set `RESPAN_LLAMA_INDEX_LIVE=1`.
Configure `RESPAN_API_KEY` in the shell or repository `.env`. Optional
`RESPAN_BASE_URL`, `RESPAN_MODEL`, and `RESPAN_EMBEDDING_MODEL` select the Gateway
endpoint and models. Live function calling and structured prediction require a
compatible model. Examples 11 and 12 retain their controlled fixtures. These
examples do not validate external vector stores, hosted workflows, remote tools,
or every provider implementation.

For local package development, install the target instrumentation after the
portable requirements:

```bash
pip install -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-llama-index
```
