# Pinecone tracing examples

These examples use the real Pinecone Python SDK and local editable Respan
instrumentation. Without Pinecone credentials they run against a bounded local
protocol fixture, so sync, async, success, and service-error paths remain
repeatable. When both `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` are set, the
round-trip example uses that existing dense-vector index and deletes only its
own unique IDs.

## Setup

```bash
cd python/tracing/pinecone
pip install -r requirements.txt -e ../../../../respan/python-sdks/instrumentations/respan-instrumentation-pinecone
```

The editable path assumes sibling `respan-example-projects` and `respan`
checkouts; substitute your adapter worktree path when using worktrees. Core
Respan dependencies remain released packages from PyPI.

Required in the repository-root `.env`:

```dotenv
RESPAN_API_KEY=...
```

Optional live Pinecone settings:

```dotenv
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=your-existing-index
PINECONE_INDEX_HOST=your-index-host
```

`PINECONE_INDEX_HOST` is required for the async live example. The expected-error
example always uses the deterministic fixture and never mutates a live index.

## Run

```bash
RESPAN_EXAMPLE_RUN_ID=my-exact-marker python run_all.py
```

The runner preserves the exact marker for all five processes, applies a
per-process timeout, continues after failures, and reports them together.

`04_documents.py` exercises Pinecone 10 document upsert, batch upsert, text search, async update/delete/fetch,
and lazy document listing across two pages against the local protocol fixture. It does not require a live index.

Before the SDK changes are released, install the requirements and local adapter in
the same resolver operation above. Core Respan packages resolve from PyPI.

`05_async_listings.py` covers lazy vector, namespace, bulk-import, and control-plane
index listings using the local fixture. No cloud service or gRPC call is made.
