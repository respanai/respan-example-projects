# Braintrust + Respan examples

The scripts use released Braintrust APIs with a local native sink and deterministic HTTP/model fixtures. They export traces to Respan, without contacting Braintrust or a model provider. Tested with Braintrust 0.44.0 and 0.5.0.

```bash
pip install -r requirements.txt
python run_all.py
```

Set `RESPAN_API_KEY` in the repository `.env` or process environment. Env files load with `override=False`; existing environment values win. `RESPAN_BASE_URL` defaults to `https://api.respan.ai/api`. The runner passes one `RESPAN_EXAMPLE_RUN_ID` to every child, continues after failures, enforces a 240-second timeout, and exits nonzero on any failure. Use only this target instrumentation editable alongside released Respan dependencies for local development.

| Example | SDK surface |
| --- | --- |
|01_basic_workflow.py|Manual native workflow and LLM records|
|02_nested_tool_workflow.py|Native task/tool/model parent tree|
|03_scored_evaluation_workflow.py|Native scores, tags and evaluation records|
|04_native_provider_calls.py|Actual wrapped OpenAI client, historical/current call IDs, 100-field tool schema and streamed chunks|
|05_full_embeddings.py|Actual provider response usage and complete 5000-dimensional embedding/tool vectors|
|06_native_generators.py|Traced functions, sync/async generators and caller OTel context|
|07_privacy_and_errors.py|Delayed parent privacy veto, source zero usage and actual error identity|
|08_customizers.py|Latest native export customizer; explicit version skip on 0.5.0|

The first three manual examples contain explicitly logged synthetic metrics. Provider usage in 04/05 comes from controlled actual SDK response objects. The fixtures establish SDK behavior and stored trace fidelity; they do not validate live Braintrust/provider credentials, Gateway eligibility, hosted evaluations/functions, datasets, attachment uploads or distributed cross-framework parenting. Each script flushes native records and shuts down Respan. The optional OpenAI fixture dependency is pinned below 3 for its verified HTTP transport API.
