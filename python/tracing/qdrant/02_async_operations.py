from _shared import points, run_scenario
from qdrant_client import AsyncQdrantClient, models


async def scenario(provider, exporter):
    client = AsyncQdrantClient(":memory:")
    try:
        await client.create_collection(
            "docs",
            vectors_config=models.VectorParams(size=4, distance=models.Distance.DOT),
        )
        await client.upsert("docs", points=points())
        if callable(getattr(client, "query_points", None)):
            result = (
                await client.query_points(
                    "docs", query=[1.0] * 4, limit=3, with_vectors=True
                )
            ).points
        else:
            result = await client.search(
                "docs", query_vector=[1.0] * 4, limit=3, with_vectors=True
            )
        count = await client.count("docs", exact=True)
        assert len(result) == count.count == 3
        await client.delete_collection("docs")
        return {"rows": len(result), "native_type": type(result[0]).__name__}
    finally:
        await client.close()


if __name__ == "__main__":
    run_scenario("async-operations", scenario)
