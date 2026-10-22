# Chroma tracing examples

Run native Chroma operations locally with Respan task spans. These scripts use a temporary persistent database, explicit vectors and a deterministic local embedding callback. They require no Chroma cloud credentials or model downloads. Every script records spans in memory by default.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_all.py
```

Run from this directory. Install the matching instrumentation wheel or branch when validating changes that have not yet been released. The SDK plugin, native Chroma and released tracing exporter are imported normally; the examples do not inject source paths.

| Script | Native feature |
|---|---|
| `01_collection_lifecycle.py` | Create/get/get-or-create/list/count/delete and heartbeat |
| `02_write_and_read.py` | Add/get/count/peek with 75 records and 5001-dimensional vectors |
| `03_query_and_filters.py` | Local embedding callback, vector query, metadata and document filters |
| `04_update_upsert_delete.py` | Native `None` returns, update/upsert/delete and metadata modification |
| `05_propagated_attributes.py` | Per-span run/scenario metadata, zero/false arguments and indexing status when exposed |
| `06_async_http.py` | Released native CLI server and AsyncHttpClient over real loopback HTTP |
| `07_privacy_and_errors.py` | Held content veto, redacted quoted credentials and unchanged native error |
| `08_pending_siblings.py` | Two native calls under the same workflow parent |

Chroma 0.5 exposes no AsyncHttpClient or indexing-status API. The corresponding optional features report their absence while all supported local scenarios run. Chroma 0.5 requires numpy 1.x; `requirements.txt` selects a compatible numpy version for both supported SDK profiles. Fork/search and attached functions may require Chroma cloud capabilities, so the examples do not pretend local engines support them.

## Explicit Respan export

Set `RESPAN_EXAMPLE_EXPORT=1` to enable the real released Respan exporter. Only that mode reads `.env` from the examples repository root. Set `RESPAN_API_KEY` there or in your environment, then run:

```bash
RESPAN_EXAMPLE_EXPORT=1 \
RESPAN_EXAMPLE_RUN_ID=chroma-my-run \
python run_all.py
```

All spans carry canonical JSON metadata plus dotted run/scenario metadata. To retain local spans and the exact HTTP bodies submitted by the released exporter, set `RESPAN_EXAMPLE_EVIDENCE_DIR` to a directory you control. The observer retains no headers or API key. HTTP success confirms ingestion transport; stored trace semantics need separate inspection.

For a single scenario, run its script directly. `run_all.py` propagates one marker across the complete suite and stops on a failed assertion. The scripts check native outcomes and database span types without rewriting native results.
