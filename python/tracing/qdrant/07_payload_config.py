from contextlib import closing

from _shared import create, points, run_scenario
from qdrant_client import QdrantClient, models


def scenario(provider, exporter):
    with closing(QdrantClient(":memory:")) as client:
        create(client)
        client.upsert("docs", points=points())
        client.set_payload("docs", payload={"updated": True}, points=[0])
        client.delete_payload("docs", keys=["text"], points=[0])
        row = client.retrieve("docs", ids=[0])[0]
        assert row.payload["updated"] is True and "text" not in row.payload
        client.overwrite_payload(
            "docs",
            payload={"flag": False, "zero": 0, "empty": "", "tag": "native"},
            points=[0],
        )
        client.create_payload_index(
            "docs", field_name="tag", field_schema=models.PayloadSchemaType.KEYWORD
        )
        updated = client.update_collection(
            "docs", optimizers_config=models.OptimizersConfigDiff(indexing_threshold=0)
        )
        config = client.get_collection("docs")
        assert config.config.params.vectors.size == 4
        row = client.retrieve("docs", ids=[0])[0]
        assert row.payload == {"flag": False, "zero": 0, "empty": "", "tag": "native"}
        return {
            "native_config_type": type(config).__name__,
            "native_update_result": updated,
            "local_index_limit": "SDK warns indexes have no effect in local mode",
        }


if __name__ == "__main__":
    run_scenario("payload-config", scenario)
