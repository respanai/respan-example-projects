# DSPy + Respan examples

These scripts exercise released DSPy 3.x APIs with deterministic model fixtures by default. They still export traces to Respan using `RESPAN_API_KEY`; fixture mode makes no model-provider requests. Tested with DSPy 3.0.0 and3.4.0.

```bash
pip install -r requirements.txt
python run_all.py
```

The runner uses one `RESPAN_EXAMPLE_RUN_ID` across every script, continues after child failures, enforces a 240-second child timeout, and exits nonzero if any script fails. Env files load with `override=False`. For local development, install only this instrumentation package editable alongside released Respan dependencies.

| Script | Released SDK surface |
| --- | --- |
|01_predict_signature.py|Signature and Predict|
|02_chain_of_thought.py|ChainOfThought|
|03_module_workflow.py|Custom Module with two predictors|
|04_tool_call.py|Direct Python Tool|
|05_react_agent.py|ReAct and a local tool|
|06_evaluate_program.py|Evaluate with a controlled devset|
|07_async_calls.py|Async Predict, model and tool callbacks|
|08_privacy_and_errors.py|Initial content opt-out and native model failure|
|09_embeddings.py|Sync and async Embedder; complete 5000-dimensional vectors|
|10_native_requests_streams.py|DSPy 3.4 lm15 Request/Response, custom engines, source usage/tool IDs and streamify|
|11_react_v2.py|DSPy 3.4 async ReActV2, source tool IDs and full tool results|

The last two scripts report a version skip on DSPy 3.0. All scripts explicitly shut down tracing. Controlled response usage is fixture data, and callable embeddings expose no provider token usage. The fixtures validate SDK behavior and stored trace fidelity; they do not establish live provider, remote interpreter, Jev, MCP-server, or Gateway eligibility.

Set `RESPAN_DSPY_MODEL_MODE=live` to opt the original model examples into Gateway calls. Set `RESPAN_DSPY_MODEL` (default `openai/gpt-4o-mini`) and `RESPAN_BASE_URL` (default `https://api.respan.ai/api`) as needed. The async/native/error/embedding feature fixtures remain deterministic. Live mode requires account/model access and is not validated by the fixture run. Existing OpenAI environment variables are preserved; credentials are passed explicitly to DSPy.
