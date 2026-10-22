# LanceDB tracing examples

These seven scripts run the actual embedded LanceDB engine against temporary
local tables. No remote database or embedding provider is used. Install the
requirements, then run:

```bash
python run_all.py
```

Local OTel recording is the default. To explicitly export controlled traces:

```bash
RESPAN_EXAMPLE_EXPORT=1 RESPAN_EXAMPLE_RUN_ID=my-lancedb-run python run_all.py
```

The `.env` file is loaded only for explicit export. Set `RESPAN_API_KEY` there or
in your environment. `RESPAN_EXAMPLE_REPORT_DIR` optionally saves local span JSON.
Export uses the released `RespanSpanExporter` and the configured Respan endpoint.

- `01_quickstart.py`: create, add, vector search, list and drop.
- `02_tables_and_merge.py`: open, update/delete, native merge builder/execution,
  scalar index and optimize, current list API where available.
- `03_queries_and_indexes.py`: Arrow/pandas/list results, filters/projections,
  query plan, native full-text index and hybrid query.
- `04_async_operations.py`: corresponding async connection/table writes, native
  synchronous merge-builder dispatch, awaited merge, indexes and query results.
- `05_full_arrow_payloads.py`: 75 rows, 5001-dimensional native vectors, explicit
  schema/metadata, false/zero and empty query result.
- `06_native_readers.py`: native sync Arrow reader iteration/read-all/close and
  context manager, plus two pending native async readers/read-all/iteration.
- `07_privacy_and_errors.py`: initial and late irreversible content vetoes with
  native results preserved, plus a real invalid-SQL engine error.

Supported native releases are tested at 0.20.0 and 0.40.0. Deprecated convenience
calls intentionally exercise the retained package boundary and forward native
warnings. Sync reader spans observe creation only: consumed rows/errors remain
unobserved while its exact C type/identity/resources and Arrow interop are kept.
Use `to_arrow`/`to_list` for full sync result capture. Async readers retain their
native public type/identity and observe only consumed batches through an owned
private iterator tap. Their native API has no public close/aclose. The adapter
never eagerly drains readers or write iterators. Existing SDK default limits and
batch-size hints are unchanged. Remote/cloud classes are outside this example
and instrumentation boundary; there is no required live-provider gate.
