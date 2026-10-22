import importlib.util
from contextlib import closing
from pathlib import Path

from qdrant_client import QdrantClient

HERE = Path(__file__).resolve().parent


def test_actual_native_local_engine_complete_values():
    spec = importlib.util.spec_from_file_location(
        "qdrant_example_shared", HERE / "_shared.py"
    )
    shared = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shared)
    with closing(QdrantClient(":memory:")) as client:
        shared.create(client)
        client.upsert("docs", points=shared.points(75))
        rows = client.retrieve("docs", ids=list(range(75)), with_vectors=True)
        assert len(rows) == 75 and all(len(x.vector) == 4 for x in rows)
        assert (
            rows[0].payload["flag"] is False
            and rows[0].payload["zero"] == 0
            and (rows[0].payload["empty"] == "")
        )
