from contextlib import closing

from _shared import create, points, run_scenario
from qdrant_client import QdrantClient


def scenario(provider, exporter):
    values = points(75, 5001)
    values[0].payload.update(
        history=[
            {
                "role": "user",
                "content": f"native history {i}",
                "tool_calls": [
                    {
                        "id": f"call-{i}",
                        "function": {
                            "name": "lookup",
                            "arguments": '{"index":0,"flag":false}',
                        },
                    }
                ],
            }
            for i in range(75)
        ],
        schema={
            "type": "object",
            "properties": {
                "private_key": {"type": "string", "default": "controlled secret"},
                "flag": {"type": "boolean", "default": False},
                "zero": {"type": "integer", "default": 0},
            },
        },
    )
    with closing(QdrantClient(":memory:")) as client:
        create(client, dimension=5001)
        client.upsert("docs", points=values)
        records = client.retrieve("docs", ids=list(range(75)), with_vectors=True)
        assert len(records) == 75 and all(len(row.vector) == 5001 for row in records)
        assert len(records[0].payload["history"]) == 75
        assert (
            records[0].payload["flag"] is False
            and records[0].payload["zero"] == 0
            and (records[0].payload["empty"] == "")
        )
        assert records[0].vector == [1.0] * 5001
        return {
            "rows": 75,
            "dimensions": 5001,
            "history": 75,
            "native_type": type(records[0]).__name__,
        }


if __name__ == "__main__":
    run_scenario("full-results", scenario)
