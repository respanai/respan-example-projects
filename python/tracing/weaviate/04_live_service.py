import os
import uuid

from _shared import run_scenario


def scenario():
    import weaviate
    from weaviate.classes.config import Configure
    from weaviate.classes.init import Auth

    url = os.environ["WEAVIATE_URL"]
    key = os.environ["WEAVIATE_API_KEY"]
    with weaviate.connect_to_weaviate_cloud(
        cluster_url=url, auth_credentials=Auth.api_key(key)
    ) as client:
        name = "RespanExample" + uuid.uuid4().hex[:12]
        col = client.collections.create(
            name, vector_config=Configure.Vectors.self_provided()
        )
        try:
            col.data.insert({"text": "explicit live example"}, vector=[0.25] * 4)
            result = col.query.near_vector(near_vector=[0.25] * 4, limit=1)
            return {"rows": len(result.objects)}
        finally:
            client.collections.delete(name)


if __name__ == "__main__":
    if os.getenv("RESPAN_EXAMPLE_LIVE") != "1":
        print("skipped=explicit live opt-in required")
    else:
        run_scenario("live-service", scenario)
