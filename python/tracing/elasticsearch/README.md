# Elasticsearch tracing examples

Run the official Elasticsearch clients against a deterministic local HTTP server.
The SDK performs its actual urllib3/aiohttp transport, serialization, response
parsing and resource cleanup. The fixture does not run an Elasticsearch engine;
it validates client and tracing behavior. No cluster, API key or export is
required by default.

The new capture/privacy behavior in these scripts requires the paired SDK
change. During review, install that checkout or its validated local wheel;
`requirements.txt` alone can resolve the older published plugin. After installing
requirements, install the paired distribution before running the scripts:

```bash
python -m pip install -r requirements.txt
python -m pip install --no-deps --force-reinstall /path/to/respan_instrumentation_elasticsearch-0.1.0-py3-none-any.whl
python run_all.py
```

| Script | Native coverage |
|---|---|
| `01_sync_client.py` | Index/get/kNN search, full 5001 dimension vectors, 75 item history, false/zero/empty |
| `02_async_client.py` | Async index/search/delete with actual aiohttp transport |
| `03_native_bulk.py` | Native streaming_bulk generator, 75 actions and NDJSON |
| `04_msearch_and_aggregations.py` | Native multi-search NDJSON and aggregation envelope |
| `05_native_response_types.py` | Object/list/text/binary/HEAD responses, empty objects and false HEAD |
| `06_native_errors_and_retries.py` | Native retry, NotFoundError and ignored HTTP 404 |
| `07_private_content.py` | Canonical content veto, native responses remain available |
| `08_transport_and_redaction.py` | Direct native Transport, settings, headers, schema and credential redaction |
| `09_live_cluster.py` | Optional actual cluster info; explicitly skipped by default |

Automatic DB spans use `task`, actual standard database/HTTP fields and full
canonical JSON input/output. They do not create embedding, model or token usage
fields. SDK helper spans remain native; Elasticsearch 8.13 does not emit the
helper wrapper span introduced by newer clients. SDK-owned attribute count
limits can bound convenience fields; full input/output are written last.

For explicit synthetic trace export, configure `RESPAN_API_KEY` in the repository
`.env` or environment and run:

```bash
RESPAN_EXAMPLE_EXPORT=1 python run_all.py
```

The `.env` is loaded only for export and existing environment values take
precedence. Optional `RESPAN_EXAMPLE_RUN_ID`, `RESPAN_EXAMPLE_LOCAL_PATH` and
`RESPAN_EXAMPLE_WIRE_PATH` record the run marker, native finished spans and actual
released exporter HTTP payload/status. Trace export does not enable a live
cluster call. For that separate opt-in:

```bash
RESPAN_ELASTICSEARCH_LIVE=1 ELASTICSEARCH_URL=http://localhost:9200 python 09_live_cluster.py
```

`ELASTICSEARCH_API_KEY` is optional for an authenticated cluster. The examples do
not administer a cluster or provision provider resources. Local fixture success
and HTTP export success are separate from stored-trace semantic verification.
