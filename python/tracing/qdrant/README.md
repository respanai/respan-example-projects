# Qdrant tracing examples

Run genuine Qdrant local-engine operations with the paired Respan instrumentation. No database service or Respan account is required for default execution. These scripts require the instrumentation source or wheel from the paired SDK change; an older published package may have different capture behavior.

Install that wheel or source checkout, then install the example dependencies and run the suite:

```bash
pip install /path/to/paired/respan_instrumentation_qdrant-0.1.0-py3-none-any.whl
pip install -r requirements.txt
python run_all.py
```

For source development, use `pip install -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-qdrant` in place of the wheel command. The package version stays unchanged until the grouped release process.

| Script | Native features |
| --- | --- |
| `01_sync_operations.py` | Local collection CRUD, upsert, query/search, count and retrieve |
| `02_async_operations.py` | Actual async client collection, upsert, query/search and cleanup |
| `03_expected_error.py` | Native missing-collection error and unchanged valid collection |
| `04_full_results.py` | 75 records, 5,001 supplied vector elements per record, 75 historical messages/tool IDs, schema defaults, false/zero/empty values |
| `05_typed_queries.py` | Named dense and sparse vectors, universal prefetch/fusion and multivector queries, payload facets |
| `06_upload_generator.py` | 75 native point models consumed exactly once by SDK upload |
| `07_payload_config.py` | Payload set/delete/overwrite, typed index/config calls and retrieved native state |
| `08_controls_http_live.py` | General suppression, real OTel sampling, bodyless content veto, actual HTTP404 decoding, separate optional live roundtrip |

Both `qdrant-client==1.19.1` and the declared minimum `1.9.0` use their genuine local engines. Current versions use `query_points`; minimum versions use native legacy `search`. Universal prefetch/fusion, matrix queries and facets skip only where the required native API is missing. Those features are not emulated. Dense and sparse queries run on both profiles.

The supplied vectors use dot-product collections, so full-result assertions compare the actual retrieved values without cosine normalization. The examples supply vectors directly; they do not call an embedding model or invent usage. SDK return values, errors and cleanup remain native. Synchronous clients use `contextlib.closing` because these SDK versions do not implement a client context manager. Async clients close with their native `close()` coroutine.

Local mode warns that payload indexes have no effect, and the local optimizer update returns its actual `False` result. The scripts retain those outcomes and check native collection settings; they do not claim server index performance or applied optimizer changes. The small HTTP handler in script 08 exercises the actual initialized remote SDK's error decoding, not a storage engine. Generator inputs are consumed solely by Qdrant; telemetry represents opaque iterable contents as null while subsequent native counts prove all 75 points were uploaded.

Default execution records spans locally. Set `RESPAN_EXAMPLE_REPORT_DIR` to save the recorded span reports. Respan export is a separate opt-in:

```bash
RESPAN_EXAMPLE_EXPORT=1 RESPAN_EXAMPLE_RUN_ID=qdrant-example-run python run_all.py
```

Provide `RESPAN_API_KEY` through the environment or repository `.env`. Only explicit export loads `.env`, and existing environment values take precedence. A unique run ID scopes later trace inspection. No credentials or headers are printed or captured by the examples.

The optional live roundtrip in script 08 skips unless `RESPAN_EXAMPLE_LIVE=1`. It requires `QDRANT_URL` and, when the service needs authentication, `QDRANT_API_KEY`. It creates a unique temporary collection and deletes it in cleanup. Live access does not enable Respan export automatically.
