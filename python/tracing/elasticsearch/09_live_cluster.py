"""Optional real cluster call; the default suite requires no cluster or key."""

import os

from _shared import run_scenario
from elasticsearch import Elasticsearch


def scenario():
    url = os.environ["ELASTICSEARCH_URL"]
    api_key = os.getenv("ELASTICSEARCH_API_KEY")
    with Elasticsearch(url, api_key=api_key, max_retries=0) as client:
        response = client.info()
        return {
            "native_response_type": type(response).__name__,
            "native_status": response.meta.status,
        }


if __name__ == "__main__":
    if os.getenv("RESPAN_ELASTICSEARCH_LIVE") != "1":
        print(
            "SKIP real cluster: set RESPAN_ELASTICSEARCH_LIVE=1 and ELASTICSEARCH_URL"
        )
    else:
        run_scenario("09_live_cluster", scenario)
