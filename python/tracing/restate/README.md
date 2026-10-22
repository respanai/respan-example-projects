# Restate Python tracing examples

Install `requirements.txt`, then run `python run_all.py`. The default runs local
controlled fixtures and needs no credentials or Restate deployment. Each fixture
uses real Restate registration, `ServerInvocationContext`, native contextvars,
serde, and `invoke_handler`. It does not simulate durable journal execution or
claim a production replay test.

The runner covers workflow and service success, native errors, VirtualObject
registration with replay-attempt context and caller cleanup, custom serde with
privacy disabled, and a terminal error carrying its real status code. Native
results are checked independently from the attempt spans. The context-manager
hook cannot observe handler response bodies, so the adapter omits them.

Set `RESPAN_EXAMPLE_EXPORT=1` to explicitly export the controlled traces using
`RESPAN_API_KEY` from the repository `.env`. `RESPAN_EXAMPLE_RUN_ID` scopes the
run, and `RESPAN_EXAMPLE_REPORT_DIR` saves local OTLP span bodies for comparison.
The exporter uses `https://api.respan.ai/api/v2/traces`. These examples make no
production service calls; there is no implicit live mode.
