from _shared import full_payload, run_scenario, server
from elasticsearch import AsyncElasticsearch


async def scenario():
    with server(
        sequence=[
            (201, {"result": "created", "_id": "doc-1"}),
            (200, full_payload()),
            (200, {"result": "deleted", "_id": "doc-1"}),
        ]
    ) as (url, requests):
        async with AsyncElasticsearch(url, max_retries=0) as client:
            created = await client.index(
                index="controlled-index",
                id="doc-1",
                document={"text": "controlled async document", "flag": False},
            )
            response = await client.search(
                index="controlled-index", query={"match_all": {}}, size=0
            )
            deleted = await client.delete(index="controlled-index", id="doc-1")
            assert (
                created.body["result"] == "created"
                and deleted.body["result"] == "deleted"
            )
            assert len(response.body["hits"]["hits"][0]["_source"]["history"]) == 75
        return {
            "native_requests": len(requests),
            "native_response_type": type(response).__name__,
        }


if __name__ == "__main__":
    run_scenario("02_async_client", scenario)
