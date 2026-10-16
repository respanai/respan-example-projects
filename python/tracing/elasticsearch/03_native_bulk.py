from _shared import run_scenario, server
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk


def scenario():
    items = [
        {
            "index": {
                "_index": "controlled-index",
                "_id": str(i),
                "status": 201,
                "result": "created",
            }
        }
        for i in range(75)
    ]
    with (
        server({"errors": False, "items": items}) as (url, requests),
        Elasticsearch(url, max_retries=0) as client,
    ):
        actions = (
            {
                "_index": "controlled-index",
                "_id": str(i),
                "_source": {
                    "text": "controlled bulk document",
                    "zero": 0,
                    "false": False,
                },
            }
            for i in range(75)
        )
        native = streaming_bulk(client, actions, chunk_size=75)
        assert type(native).__name__ == "generator"
        outcomes = list(native)
        assert len(outcomes) == 75 and all(ok for ok, _ in outcomes)
        assert len(requests) == 1 and requests[0]["body"].count(b"\n") == 150
        return {"native_items": 75, "native_requests": len(requests)}


if __name__ == "__main__":
    run_scenario("03_native_bulk", scenario)
