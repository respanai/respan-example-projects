# Temporal tracing examples

Run four controlled examples against Temporal's actual ephemeral time-skipping server. Local mode uses an in-memory exporter and needs no Respan credential.

```bash
pip install -r requirements.txt
RESPAN_EXAMPLE_RUN_ID=temporal-check python run_all.py
```

The examples cover workflow/activity success, a non-retried activity failure, signal/query propagation, history replay, complete nested payloads, private workflow inputs and native cancellation. Each script asserts the native result and shuts down telemetry. `RESPAN_EXAMPLE_REPORT_DIR` writes local span reports. The runner preserves your run marker and reports all script failures.

Temporal downloads its local test-server binary on first use. A download or startup failure is a local runtime prerequisite failure; `TEMPORAL_TEST_SERVER_PATH` can select an existing compatible binary.

To export the synthetic spans to Respan, configure `RESPAN_API_KEY` in the repository's `.env` and opt in:

```bash
RESPAN_EXAMPLE_RUN_ID=temporal-export-check python run_all.py --export
```

Export uses `https://api.respan.ai/api/v2/traces`. Each span carries deliberately assigned synthetic run labels, including private fixture spans whose customer content is suppressed. Export success and stored-trace inspection are separate checks.

To use your own Temporal server, supply its address explicitly. `TEMPORAL_NAMESPACE` defaults to `default`; the server must allow the example workflows and activities:

```bash
python run_all.py --remote-address localhost:7233
```

For local SDK development, install only the target instrumentation as an editable dependency after the registry requirements:

```bash
pip install -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-temporal
```

Temporal's native cancellation path can finish a waiting workflow without a `CompleteWorkflow` span. Replay does not add workflow spans, and client query spans carry the actual query result.
