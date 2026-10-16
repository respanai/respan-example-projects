from _shared import run_scenario, server
from elasticsearch import Elasticsearch


def scenario():
    types = []
    for body, content_type in [
        ([{"flag": False, "zero": 0}], "application/json"),
        ("controlled text response", "text/plain"),
        (b"controlled\x00binary", "application/vnd.mapbox-vector-tile"),
        ({}, "application/json"),
    ]:
        with (
            server(body, content_type=content_type) as (url, _),
            Elasticsearch(url, max_retries=0) as client,
        ):
            response = client.perform_request(
                "GET", "/controlled", endpoint_id="controlled"
            )
            assert response.body == body
            types.append(type(response).__name__)
    with server(status=404) as (url, _), Elasticsearch(url, max_retries=0) as client:
        response = client.exists(index="controlled-index", id="missing")
        assert response.body is False
        types.append(type(response).__name__)
    return {"native_types": types}


if __name__ == "__main__":
    run_scenario("05_native_response_types", scenario)
