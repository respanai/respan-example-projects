from _shared import run_scenario, server
from elasticsearch import Elasticsearch, NotFoundError


def scenario():
    with (
        server(
            sequence=[
                (503, {"error": "controlled retry"}),
                (200, {"hits": {"hits": []}, "took": 0}),
            ]
        ) as (url, requests),
        Elasticsearch(url, max_retries=1, retry_on_status=[503]) as client,
    ):
        response = client.search(index="controlled-index", query={"match_all": {}})
        assert response.meta.status == 200 and len(requests) == 2
    with (
        server(
            {
                "error": {
                    "type": "index_not_found_exception",
                    "reason": "controlled missing document",
                },
                "status": 404,
            },
            status=404,
        ) as (url, _),
        Elasticsearch(url, max_retries=0) as client,
    ):
        try:
            client.get(index="missing", id="doc-1")
        except NotFoundError as error:
            assert error.meta.status == 404
        else:
            raise AssertionError("native NotFoundError expected")
        ignored = client.options(ignore_status=404).get(index="missing", id="doc-1")
        assert ignored.body["status"] == 404
    return {
        "retry_requests": 2,
        "native_error_type": "NotFoundError",
        "ignored_status": 404,
    }


if __name__ == "__main__":
    run_scenario("06_native_errors_and_retries", scenario)
