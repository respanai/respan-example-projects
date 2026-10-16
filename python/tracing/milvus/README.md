# Milvus tracing examples

Run actual PyMilvus clients against the released Milvus Lite gRPC engine. The scripts start an isolated native server on loopback and record spans in memory by default. No Respan key, cloud server or model download is needed for local runs.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_all.py
```

Run from this directory. Before the companion SDK changes are released, install the matching built instrumentation wheel or branch for validation. The examples import installed SDK packages normally and do not inject source paths.

| Script | Native feature |
|---|---|
| `01_collection_lifecycle.py` | Explicit schema, create/describe/has/list/drop |
| `02_data_operations.py` | 75 records with 5001-dimensional vectors, query/get/upsert/delete |
| `03_expected_error.py` | Unchanged native missing-collection error |
| `04_hybrid_search.py` | Native AnnSearchRequest/RRFRanker, FLAT index and hybrid result |
| `05_iterator_lifecycle.py` | Native query iterator batches and closure |
| `06_async_client.py` | Actual AsyncMilvusClient over loopback gRPC |
| `07_privacy_and_siblings.py` | Held privacy veto, quoted credentials and same-parent native calls |
| `08_native_task.py` | Native OptimizeTask handle and exact SDK ParamError |

The recommended local profile is PyMilvus 3.0.2 with Milvus Lite 3.2.1. The instrumentation also supports SDK 2.4.1, which has no local `.db` URI, async/client iterator/hybrid/optimization APIs. Those features report genuine absence. For that older client, use a compatible server URI via `RESPAN_MILVUS_URI`, or set `RESPAN_MILVUS_LITE_EXECUTABLE` to a released Lite executable in a separate current SDK environment. Its imports require `setuptools<81` and `marshmallow<4`; do not run current Lite's server with old SDK protobuf classes. These are native compatibility limits rather than instrumentation shims.

Use a fresh database for each controlled run. If you provide `RESPAN_MILVUS_URI`, the scenarios create/delete collections with controlled names on that server. Cloud-only features retain their native capability errors. Native Lite may use its existing client timestamp fallback for iterators; the scripts do not rewrite that behavior.

## Explicit Respan export

Only `RESPAN_EXAMPLE_EXPORT=1` loads `.env` from the examples repository root and enables the released Respan exporter. Put `RESPAN_API_KEY` there or in your environment:

```bash
RESPAN_EXAMPLE_EXPORT=1 \
RESPAN_EXAMPLE_RUN_ID=milvus-my-run \
python run_all.py
```

Every actual span carries canonical JSON and dotted run/scenario metadata. Set `RESPAN_EXAMPLE_EVIDENCE_DIR` to retain local spans and exact bodies submitted through the real exporter's session. Headers and keys are not retained. HTTP success is a transport result; inspect stored traces separately for semantic acceptance.

Run any script individually, or use `run_all.py` for one shared run marker across the complete mapped suite. The runner stops on a failed native assertion.
