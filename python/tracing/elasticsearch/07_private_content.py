from _shared import full_payload, run_scenario, server
from elasticsearch import Elasticsearch
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def scenario():
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        with (
            server(full_payload()) as (url, _),
            Elasticsearch(url, max_retries=0) as client,
        ):
            response = client.search(
                index="private-controlled-index",
                body={"query": {"match": {"text": "private controlled request"}}},
            )
            assert len(response.body["hits"]["hits"][0]["_source"]["vector"]) == 5001
            head = client.exists(
                index="private-controlled-index", id="private-controlled-id"
            )
            assert head.body is True
    finally:
        context.detach(token)
    return {"native_calls": 2, "canonical_content_captured": False}


if __name__ == "__main__":
    run_scenario("07_private_content", scenario)
