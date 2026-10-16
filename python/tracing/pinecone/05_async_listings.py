"""Current SDK lazy async vector, namespace, import, and index listings."""

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
from pinecone import AsyncPinecone
from pinecone.async_client.async_index import AsyncIndex
from respan import Respan, workflow

WORKFLOW_NAME = "pinecone_async_listings_workflow"


@workflow(name=WORKFLOW_NAME)
async def run_listings():
    host = loopback_host()
    async with AsyncIndex(host=host, api_key="fixture-key") as index:
        vectors = [
            vector.id
            async for page in index.list(namespace="demo")
            for vector in page.vectors
        ]
        namespaces = [
            namespace.name
            async for page in index.list_namespaces()
            for namespace in page.namespaces
        ]
        imports = [item.id async for item in index.list_imports()]
    async with AsyncPinecone(host=host, api_key="fixture-key") as client:
        indexes = [index.name for index in await client.indexes.list().to_list()]
    return {
        "vector_ids": vectors,
        "namespaces": namespaces,
        "import_ids": imports,
        "indexes": indexes,
    }


def main():
    run_marker = marker()
    respan = create_respan(WORKFLOW_NAME, run_marker)
    try:
        with Respan.propagate_attributes(
            **workflow_attributes(WORKFLOW_NAME, run_marker, execution_id())
        ):
            result = asyncio.run(run_listings())
        print_result(WORKFLOW_NAME, result, run_marker)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
