# Weaviate tracing examples

Run initialized Weaviate v4 clients against local HTTP and gRPC protocol handlers. These examples exercise the released SDK's actual request serialization, typed responses, async execution, errors, tenant/config APIs and batch protocol without a Weaviate service or Respan account.

```bash
pip install -r requirements.txt
python run_all.py
```

| Script | Native features |
| --- | --- |
| `01_sync_operations.py` | Collection create/delete, HTTP insert, gRPC vector query and aggregate |
| `02_async_operations.py` | Async collection, insert, hybrid query and aggregate |
| `03_expected_error.py` | Native gRPC and HTTP service errors |
| `04_live_service.py` | Explicit real-service create/insert/query/delete |
| `05_full_results.py` | 75 typed objects with 5,001 supplied vector elements each |
| `06_config_tenants.py` | Native property/config models, tenant operations and collection listing |
| `07_privacy.py` | Quoted credentials, schema defaults, false/zero and bodyless private query |
| `08_batch_and_iteration.py` | 75-object bidirectional ingest and lazy native query pagination |

Default execution records spans locally. To send the same controlled scenarios to Respan, set `RESPAN_API_KEY`, `RESPAN_EXAMPLE_EXPORT=1` and a unique `RESPAN_EXAMPLE_RUN_ID`. Only explicit export loads the repository `.env`; existing environment values take precedence. `RESPAN_EXAMPLE_REPORT_DIR` saves the actual locally recorded spans. Do not put credentials in saved span content.

```bash
RESPAN_EXAMPLE_EXPORT=1 RESPAN_EXAMPLE_RUN_ID=weaviate-example-run python run_all.py
```

The live script skips unless `RESPAN_EXAMPLE_LIVE=1`. It then requires `WEAVIATE_URL` and `WEAVIATE_API_KEY`, creates a unique temporary collection, and deletes it in cleanup. Export is independent of live access.

The local handlers return controlled protocol values, including supplied vectors; they do not implement a Weaviate storage engine, vector generation or relevance/consistency semantics. The examples preserve native typed return values and client cleanup. Collection iterators retain native identity and are traced per executed page. Batch queue and flush operations remain SDK boundaries; only the native outer `ingest` result establishes its returned batch outcome. Unknown input generators are not drained by telemetry, so their content is structural while the complete native batch result is retained.
