from contextlib import closing

from _shared import create, points, query, run_scenario
from qdrant_client import QdrantClient


def scenario(provider, exporter):
    with closing(QdrantClient(":memory:")) as client:
        create(client)
        client.upsert("docs", points=points())
        result = query(client)
        count = client.count("docs", exact=True)
        found = client.retrieve("docs", ids=[0], with_vectors=True)
        assert len(result) == count.count == 3 and found[0].payload["flag"] is False
        client.delete_collection("docs")
        return {
            "rows": len(result),
            "count": count.count,
            "native_type": type(result[0]).__name__,
        }


if __name__ == "__main__":
    run_scenario("sync-operations", scenario)
