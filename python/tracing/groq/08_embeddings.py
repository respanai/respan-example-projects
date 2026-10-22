"""Embedding vectors, both float and base64 encodings, sync and async."""

from _shared import make_async_client, make_client, run_example


async def scenario():
    with make_client() as client:
        response = client.embeddings.create(
            model="nomic-embed-text-v1_5",
            input=["synthetic embedding"],
            encoding_format="float",
        )
        count = len(response.data)
    async with make_async_client() as client:
        raw = await client.embeddings.with_raw_response.create(
            model="nomic-embed-text-v1_5",
            input="synthetic embedding",
            encoding_format="base64",
        )
        await raw.parse()
        await raw.close()
    return {"embedding_count": count}


if __name__ == "__main__":
    run_example("embeddings", scenario)
