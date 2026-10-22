from contextlib import closing

from _shared import run_scenario
from qdrant_client import QdrantClient, models


def scenario(provider, exporter):
    with closing(QdrantClient(":memory:")) as client:
        client.create_collection(
            "typed",
            vectors_config={
                "dense": models.VectorParams(size=4, distance=models.Distance.DOT)
            },
            sparse_vectors_config={"sparse": models.SparseVectorParams()},
        )
        client.upsert(
            "typed",
            points=[
                models.PointStruct(
                    id=i,
                    vector={
                        "dense": [float(i + 1), 0.0, 0.0, 0.0],
                        "sparse": models.SparseVector(
                            indices=[0, 2], values=[float(i + 1), 0.5]
                        ),
                    },
                    payload={"tag": "native", "flag": False, "zero": 0},
                )
                for i in range(3)
            ],
        )
        if callable(getattr(client, "query_points", None)):
            dense = client.query_points(
                "typed",
                query=[1.0, 0.0, 0.0, 0.0],
                using="dense",
                limit=3,
                with_vectors=True,
            ).points
            sparse = client.query_points(
                "typed",
                query=models.SparseVector(indices=[0, 2], values=[1.0, 0.5]),
                using="sparse",
                limit=3,
                with_vectors=True,
            ).points
        else:
            dense = client.search(
                "typed",
                query_vector=models.NamedVector(
                    name="dense", vector=[1.0, 0.0, 0.0, 0.0]
                ),
                limit=3,
                with_vectors=True,
            )
            sparse = client.search(
                "typed",
                query_vector=models.NamedSparseVector(
                    name="sparse",
                    vector=models.SparseVector(indices=[0, 2], values=[1.0, 0.5]),
                ),
                limit=3,
                with_vectors=True,
            )
        assert len(dense) == len(sparse) == 3 and sparse[0].vector[
            "sparse"
        ].indices == [0, 2]
        capabilities = {"dense": len(dense), "sparse": len(sparse)}
        if (
            callable(getattr(client, "query_points", None))
            and hasattr(models, "FusionQuery")
            and hasattr(models, "Prefetch")
        ):
            fused = client.query_points(
                "typed",
                prefetch=[
                    models.Prefetch(query=[1.0, 0.0, 0.0, 0.0], using="dense", limit=3),
                    models.Prefetch(
                        query=models.SparseVector(indices=[0, 2], values=[1.0, 0.5]),
                        using="sparse",
                        limit=3,
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=3,
            ).points
            assert len(fused) == 3
            capabilities["fusion"] = 3
            client.create_collection(
                "multi",
                vectors_config=models.VectorParams(
                    size=2,
                    distance=models.Distance.DOT,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    ),
                ),
            )
            client.upsert(
                "multi",
                points=[
                    models.PointStruct(
                        id=1, vector=[[1.0, 0.0], [0.0, 1.0]], payload={"native": True}
                    )
                ],
            )
            multi = client.query_points(
                "multi", query=[[1.0, 0.0], [0.0, 1.0]], limit=1, with_vectors=True
            ).points
            assert multi[0].vector == [[1.0, 0.0], [0.0, 1.0]]
            capabilities["multivector"] = 1
        else:
            capabilities.update(
                fusion="skipped: native universal query API absent",
                multivector="skipped: native universal matrix query API absent",
            )
        if callable(getattr(client, "facet", None)):
            facets = client.facet("typed", key="tag", exact=True)
            assert facets.hits[0].count == 3
            capabilities["facet"] = 3
        else:
            capabilities["facet"] = "skipped: native facet API absent"
        return capabilities


if __name__ == "__main__":
    run_scenario("typed-queries", scenario)
