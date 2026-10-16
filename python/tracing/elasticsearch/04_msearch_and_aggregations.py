from _shared import full_payload, run_scenario, server
from elasticsearch import Elasticsearch


def scenario():
    responses = [
        full_payload(),
        {
            "took": 0,
            "hits": {"hits": []},
            "aggregations": {"flags": {"buckets": [{"key": False, "doc_count": 0}]}},
            "empty": "",
        },
    ]
    with (
        server({"responses": responses}) as (url, requests),
        Elasticsearch(url, max_retries=0) as client,
    ):
        result = client.msearch(
            searches=[
                {"index": "controlled-index"},
                {"query": {"match_all": {}}},
                {"index": "controlled-index"},
                {"size": 0, "aggs": {"flags": {"terms": {"field": "flag"}}}},
            ]
        )
        assert (
            len(result.body["responses"]) == 2
            and result.body["responses"][1]["empty"] == ""
        )
        assert requests[0]["body"].count(b"\n") == 4
        return {"native_requests": len(requests), "native_response_count": 2}


if __name__ == "__main__":
    run_scenario("04_msearch_and_aggregations", scenario)
