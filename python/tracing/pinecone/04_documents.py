"""Pinecone 10 document operations through the released SDK and a local fixture."""

import asyncio

from _loopback import loopback_host
from _shared import (
    create_respan,
    execution_id,
    finish_respan,
    marker,
    print_result,
    workflow_attributes,
)
from pinecone import Index, TextQuery
from pinecone.async_client.async_index import AsyncIndex
from respan import Respan, workflow

WORKFLOW_NAME = "pinecone_documents_workflow"


@workflow(name=WORKFLOW_NAME)
async def run_documents():
    host = loopback_host()
    with Index(host=host, api_key="fixture-key") as index:
        upsert = index.documents.upsert(
            namespace="demo", documents=[{"_id": "doc-1", "title": "tracing"}]
        )
        batched = index.documents.batch_upsert(
            namespace="demo",
            documents=[{"_id": "doc-2", "title": "tracing"}],
            show_progress=False,
        )
        search = index.documents.search(
            namespace="demo",
            score_by=[TextQuery(query="tracing", fields=["title"])],
            top_k=1,
        )
    async with AsyncIndex(host=host, api_key="fixture-key") as index:
        await index.documents.update(
            namespace="demo", documents=[{"_id": "doc-1", "title": "updated"}]
        )
        listed = await index.documents.list(namespace="demo").to_list()
        await index.documents.delete(namespace="demo", ids=["doc-2"])
        fetched = await index.documents.fetch(namespace="demo", ids=["doc-1"])
    return {
        "upserted_count": upsert.upserted_count,
        "listed_ids": [document.id for document in listed],
        "batch_success": batched.has_errors is False,
        "match": search.matches[0].title,
        "document": fetched.documents["doc-1"].title,
    }


def main():
    run_marker = marker()
    respan = create_respan(WORKFLOW_NAME, run_marker)
    try:
        with Respan.propagate_attributes(
            **workflow_attributes(WORKFLOW_NAME, run_marker, execution_id())
        ):
            result = asyncio.run(run_documents())
        print_result(WORKFLOW_NAME, result, run_marker)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
