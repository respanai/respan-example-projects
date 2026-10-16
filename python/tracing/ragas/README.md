# Ragas tracing examples

These scripts use released Ragas 0.4.3 APIs, native typed metrics/evaluation results/executors/datasets, and genuine application callbacks. The native LLM script uses real OpenAI/AsyncOpenAI clients and `ragas.llm_factory` against a controlled localhost HTTP endpoint. Default execution records spans locally without Respan or provider credentials. Native Ragas analytics are disabled before imports.

```bash
python -m pip install -r requirements.txt
python run_all.py
```

Use `langchain-community>=0.3,<0.4`. Ragas 0.4.3 imports `ChatVertexAI` from the old Community namespace; the newest Community 0.4.2 fails in the bare SDK. Local current validation uses compatible released Community 0.3.31. The instrumentation checkout remains version 0.1.0; no facade version is required.

| Script | Actual native scenario |
| --- | --- |
| `01_modern_metrics.py` | collection `score`/`ascore`, complete 75-item `batch_score`/`abatch_score` |
| `02_evaluate.py` | typed `evaluate`/`aevaluate`, legacy ExactMatch, connected metric children |
| `03_experiment.py` | sync/async app callbacks, direct experiment calls, `arun`, InMemoryBackend/Dataset and false/zero/empty |
| `04_decorated_metrics.py` | numeric/discrete/ranking decorators created after activation, untraced raw callback, full 5001 ranking |
| `05_deferred_executors.py` | original lazy Executor, `results`/`aresults`/`cancel`, no fabricated cancelled output |
| `06_complete_metric_result.py` | native MetricResult identity, full nested 75 history/5001 NumPy vector, empty reason/false/zero |
| `07_expected_error.py` | native validation AssertionError, SDK-caught callback error returned as MetricResult |
| `08_content_policy.py` | canonical late and initial ancestor content veto without changing native results |
| `09_native_llm.py` | four SimpleLLMMetric methods with real OpenAI sync/async clients and six local HTTP requests |

All scripts use `RagasInstrumentor(tracer_provider=provider)` with the application's native OTel provider. No vendor modules/methods are replaced. Native task spans retain sourced input/output without guessed model/token/HTTP fields. The OpenAI endpoint returns controlled structured JSON with numeric value 0 and empty reason; no paid provider is contacted. Raw decorated `metric(...)` callbacks retain native behavior without a metric span; call `score` or `ascore` for traced scoring.

Optional trace export is explicit and independent of provider access:

```bash
RESPAN_EXAMPLE_ENV_FILE=/absolute/path/to/.env \
RESPAN_EXAMPLE_RUN_ID=ragas-controlled-run \
python run_all.py --export
```

`RESPAN_EXAMPLE_EXPORT=1` is equivalent to `--export`. The `.env` loads only for explicit export; configure `RESPAN_API_KEY`. The released `RespanSpanExporter` uses `RESPAN_TRACE_ENDPOINT`, defaulting to `https://api.respan.ai/api/v2/traces`. `RESPAN_EXAMPLE_WIRE_PATH` records its actual HTTP body/status and `RESPAN_EXAMPLE_LOCAL_PATH` records same-run local spans. Use controlled synthetic content for these artifacts. Stored trace projection acceptance is separate from native local/example/export success.

For cancelled/unconsumed native executors, applications own native coroutine job cleanup. The examples close unstarted native coroutine jobs when applicable. Provider/environment limits remain those of the native SDK. Keep async clients, executor consumption, and provider/instrumentor shutdown in application cleanup paths as shown.
