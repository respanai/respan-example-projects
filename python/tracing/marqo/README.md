# Marqo tracing examples

These scripts exercise the released Marqo Python client against a controlled
loopback HTTP service. They retain native SDK requests, typed configuration,
results and exceptions. No hosted Marqo account or Marqo API key is required.
The service supplies synthetic records and vectors; this is client compatibility
validation rather than hosted-service acceptance.

## Run

```bash
cd python/tracing/marqo
python -m pip install -r requirements.txt
python run_all.py
```

Install the matching instrumentation wheel from the companion SDK checkout when
validating changes that have not yet been released.

The default run checks traces in memory and makes no Respan request. To export
the same synthetic cases, set `RESPAN_API_KEY` in the repository-root `.env` and
opt in explicitly:

```bash
RESPAN_EXAMPLE_RUN_ID=marqo-controlled python run_all.py --export
```

`RESPAN_EXAMPLE_ENV_FILE` selects another environment file. Each operation
carries `run_id`, `example_set` and `example_case` metadata. Optional
`RESPAN_EXAMPLE_LOCAL_PATH` and `RESPAN_EXAMPLE_WIRE_PATH` record local spans and
actual exporter requests as JSONL; exported payloads contain the synthetic
content. All scripts flush and shut down their provider, deactivate owned
instrumentation and stop their loopback server.

## Cases

| Script | Native feature and trace assertions |
| --- | --- |
| `01_quickstart.py` | Create, write 75 records, search and delete; native aliases emit one operation span. |
| `02_service_error.py` | Native 503 exception, sanitized diagnostic, actual error status and no invented output. |
| `03_embeddings.py` | Complete 5,001-value embedding, observed model, nonvector envelope and false/zero/empty fields. |
| `04_documents_batches.py` | Native threaded batching, complete public records/vectors and aggregate results, get/get-many/delete. |
| `05_search_recommend_bulk.py` | Weighted and filtered search, recommend and typed bulk requests. |
| `06_settings_and_models.py` | Native settings, stats, listing and version-compatible model ejection. |
| `07_content_policy.py` | Initial canonical and ancestor denial, unchanged SDK results, cleared bodies/events/diagnostics. |

Validated with Marqo 3.18.2 and 3.5.1. Minimum-version model ejection retains its
required `model_device` argument. Factory calls `index` and `get_index` do not
create operation spans. Native worker requests can run outside the active call
context; public batch inputs and aggregate results remain complete, but an
unobserved worker request does not acquire invented HTTP status or metadata.

Local spans, actual exporter payloads and stored Respan logs are separate checks.
Successful HTTP export alone does not prove stored field or error fidelity.
