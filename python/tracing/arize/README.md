# Arize tracing examples

The nine scripts execute released Arize SDK code against controlled urllib3 and
requests-futures transport responses. Public SDK methods are not replaced.
Generated REST parsing, protobuf request construction, native Future behavior,
and the SDK's experiment helper remain in use. Default runs need no credentials
and export no traces or Arize requests to a service.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
RESPAN_EXAMPLE_RUN_ID=arize-check python run_all.py
```

The suite covers historical span reads with full vectors and tool-call data,
ML uploads, dataset creation, an actual dry-run experiment, prompt/evaluator/admin
pages, newer REST resource clients and dataset mutations, private content, and
native synchronous/Future errors. SDK 8.35.0 explicitly skips newer resource and
dataset mutation APIs it does not expose. SDK 8.57.0 exercises all nine scripts.

Every child uses the shell's exact run marker. The runner continues after failures
or timeouts and returns an aggregate status. Environment files load with
`override=False`. Each initialized Respan client flushes and shuts
down in `finally`.

To export these controlled traces to Respan, set `RESPAN_ARIZE_EXPORT=1`
and `RESPAN_API_KEY`. The default Respan base URL is
`https://api.respan.ai/api`. Arize requests still use the fixtures;
these examples never write to a live Arize account.

Arize marks several released REST APIs as alpha/beta. The adapter records
control-plane task operations; historical LLM/tool data is preserved as payload
data and does not become new model usage or tool execution spans. The experiment
SDK keeps its native worker tracing configuration. Live Arize Flight uploads,
remote agents/evaluators, webhook delivery, and every administrative mutation
are outside this controlled suite.
