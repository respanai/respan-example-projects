from contextlib import closing

from _shared import create, points, run_scenario
from qdrant_client import QdrantClient


def scenario(provider, exporter):
    with closing(QdrantClient(":memory:")) as client:
        create(client)
        try:
            client.upsert("missing", points=points())
        except ValueError as error:
            kind = type(error).__name__
        else:
            raise AssertionError("native missing collection error required")
        count = client.count("docs", exact=True)
        assert count.count == 0
        return {"native_error": kind, "original_collection_count": count.count}


if __name__ == "__main__":
    run_scenario("expected-error", scenario)
