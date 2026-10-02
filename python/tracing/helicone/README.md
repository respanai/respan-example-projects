# Helicone Python tracing examples

These examples exercise the published `helicone-helpers==1.2.1`
`HeliconeManualLogger` and `HeliconeLogBuilder` APIs through
`respan-instrumentation-helicone`.

The deterministic suite covers:

- sync LLM `log_request` with model, messages, usage, and safe correlation headers
- LLM tool definitions and current-turn tool calls
- text completion and embedding value/vector contracts
- async builder streaming with first-token timing
- successful non-stream builder `add_model()` / `add_response()` logging
- builder cancellation with canonical error type and HTTP 499 status
- delayed builder export with creation-time parent/correlation context
- builder error logging
- documented `log_request` chunk streams and Anthropic streaming events
- Google `contents` / `candidates` / `usageMetadata` custom-logger shapes
- `capture_content=False` identity/usage-only spans
- nested direct success plus outer callback failure
- Helicone `_type=tool`, `_type=vector_db`, and `_type=data` events
- direct Anthropic-shaped `send_log`
- the Helicone 1.2.1 `log_request` error fallback, where the SDK itself skips its sink
- one optional live Helicone logging call when `HELICONE_API_KEY` is configured

The correctness runner is deterministic and excludes the optional live script.
Run the latter directly when desired:

```bash
python python/tracing/helicone/09_live_helicone.py
```

Helicone Helpers 1.2.1 swallows transport exceptions and non-200 responses, so
that script reports only that a live log was attempted. It is not proof that
Helicone accepted the record; verify acceptance in Helicone separately.

Activate this manual-logger instrumentation explicitly. Do not also activate an
overlapping provider instrumentation for the wrapped provider operation unless
two spans for the same logical call are intentional.

Deterministic examples send Helicone traffic only to a bounded localhost fixture;
they never use a configured Helicone credential. All examples still export their
Respan trace spans to the configured Respan platform.

After `respan-instrumentation-helicone` is published, install the
registry-portable requirements and run the suite:

```bash
python -m pip install -r python/tracing/helicone/requirements.txt
RESPAN_EXAMPLE_RUN_ID=helicone-check python python/tracing/helicone/run_all.py
```

Before the first registry release, install the already-published dependencies
and link the local package explicitly:

```bash
python -m pip install "helicone-helpers==1.2.1" "python-dotenv>=1,<2" "respan-ai>=4.1,<5"
python -m pip install --no-deps -e ../respan/python-sdks/instrumentations/respan-instrumentation-helicone
RESPAN_EXAMPLE_RUN_ID=helicone-local python python/tracing/helicone/run_all.py
```

Every script preserves the exact shell marker, uses bounded semantic workflow
arguments, flushes and shuts down Respan, and closes the local fixture. The
aggregate runner continues through failures and timeouts.
