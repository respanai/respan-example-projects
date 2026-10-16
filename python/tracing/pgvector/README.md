# pgvector native tracing examples

Run actual released pgvector/psycopg clients against an isolated genuine
PostgreSQL engine. The `pgserver` wheel supplies native binaries and a vector
extension; each scenario creates a temporary data directory, starts the engine,
closes native resources and stops it. No Docker, global service, database
credentials or export is required by default. No vendor modules are replaced.

The new capture/privacy behavior requires the paired SDK change. During review,
install the paired checkout or validated local wheel after requirements;
requirements alone can resolve the older published plugin:

```bash
python -m pip install -r requirements.txt
python -m pip install --no-deps --force-reinstall /path/to/respan_instrumentation_pgvector-0.1.0-py3-none-any.whl
python run_all.py
```

| Script | Actual native coverage |
|---|---|
| `01_sync_similarity.py` | Sync register/execute/fetch,75rows×5001vectors,75history,false/zero/empty,actual L2 distance |
| `02_async_similarity.py` | Async registration/execute/fetch/closure and cosine query |
| `03_bulk_returning.py` | Native75-item generator consumed once,executemany null,RETURNING/nextset,rollback |
| `04_server_cursors.py` | Original sync/async named server cursors,fetchmany/fetchall,closure |
| `05_native_vector_types.py` | Vector/half-vector/sparse-vector/bit with5001dimensions and real type capability checks |
| `06_native_errors_and_empty.py` | Native UndefinedTable/SQLSTATE,error preservation,empty/null,false/zero/empty,SQL composition |
| `07_private_content.py` | Canonical privacy veto; actual native vector still returned |
| `08_native_registration_and_redaction.py` | Actual psycopg2 registration and credential-column/JSON/schema/text/URL capture redaction |
| `09_live_postgres.py` | Explicit optional existing-server registration/query, skipped by default |

The pgserver0.1.4 wheel bundles PostgreSQL16.2 and pgvector extension0.6.2.
Half/sparse types need extension0.7+; the script explicitly reports absent native
types as capability skips. The validated current/minimum/clean-wheel suite used
an isolated build of official extension0.8.7 against the bundled headers. To
select another isolated native binary installation with its extension installed:

```bash
PGVECTOR_POSTGRES_BIN=/path/to/isolated/postgres/bin python run_all.py
```

Automatic database spans are TASK with actual upstream DB/query/server fields,
full canonical rows/parameters/native metadata and no generated embeddings,
models,tokens or fake HTTP status. Native cursor iteration and custom/unknown
parameter iterators remain under the driver; the adapter does not drain them.
Sparse capture retains all indices/values/dimensions; bit/bytes reflect the
actual native return format. No adapter preview cap applies.

For explicit controlled synthetic trace export, configure `RESPAN_API_KEY` in
the repository `.env` or environment:

```bash
RESPAN_EXAMPLE_EXPORT=1 python run_all.py
```

`.env` loads only when exporting; existing environment values take precedence.
Optional `RESPAN_EXAMPLE_RUN_ID`, `RESPAN_EXAMPLE_LOCAL_PATH` and
`RESPAN_EXAMPLE_WIRE_PATH` retain the marker, real finished spans and actual
released exporter HTTP payload/status. Export does not enable live-server work.
For that separate opt-in, configure a server whose vector extension is installed:

```bash
RESPAN_PGVECTOR_LIVE=1 PGVECTOR_DSN='your existing connection string' python 09_live_postgres.py
```

The live script does not provision an external database or extension. Local
native engine success, trace export and scoped stored-trace semantic acceptance
are separate gates.
