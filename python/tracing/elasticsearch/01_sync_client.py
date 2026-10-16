from _shared import full_payload, run_scenario, server
from elasticsearch import Elasticsearch


def scenario():
    document = {
        "text": "controlled native document",
        "vector": [0.0] * 5001,
        "history": [{"position": i} for i in range(75)],
        "false": False,
        "zero": 0,
        "empty": "",
    }
    with (
        server(
            sequence=[
                (201, {"result": "created", "_id": "doc-1"}),
                (200, {"found": True, "_source": document}),
                (200, full_payload()),
            ]
        ) as (url, requests),
        Elasticsearch(url, max_retries=0) as client,
    ):
        created = client.index(
            index="controlled-index", id="doc-1", document=document, refresh=False
        )
        fetched = client.get(index="controlled-index", id="doc-1")
        found = client.search(
            index="controlled-index",
            knn={
                "field": "vector",
                "query_vector": [0.0] * 5001,
                "k": 1,
                "num_candidates": 1,
            },
            request_cache=False,
        )
        assert len(found.body["hits"]["hits"][0]["_source"]["vector"]) == 5001
        assert (
            fetched.body["_source"] == document and created.body["result"] == "created"
        )
        return {
            "native_requests": len(requests),
            "vector_dimensions": 5001,
            "history_items": 75,
        }


if __name__ == "__main__":
    run_scenario("01_sync_client", scenario)
