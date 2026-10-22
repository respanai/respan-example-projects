from contextlib import closing

from _shared import create, points, run_scenario
from qdrant_client import QdrantClient


def scenario(provider, exporter):
    with closing(QdrantClient(":memory:")) as client:
        create(client)
        consumed = 0

        def supplied():
            nonlocal consumed
            for point in points(75):
                consumed += 1
                yield point

        result = client.upload_points(
            "docs", points=supplied(), batch_size=16, parallel=1, wait=True
        )
        assert result is None and consumed == 75
        count = client.count("docs", exact=True)
        assert count.count == 75
        return {
            "native_uploaded": count.count,
            "generator_consumed": consumed,
            "native_return": result,
        }


if __name__ == "__main__":
    run_scenario("upload-generator", scenario)
