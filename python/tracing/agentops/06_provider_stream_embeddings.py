"""Native provider streaming and sync/async full embedding responses."""

import asyncio

from _fixtures import provider_clients
from _shared import build_respan
from agentops import trace


def main():
    telemetry = build_respan(
        example_name="stream-embeddings", workflow_name="agentops_stream_embeddings"
    )
    sdk, client, async_client = provider_clients()

    @trace(name="stream_embedding_workflow")
    def run():
        stream = client.chat.completions.create(
            model="fixture-chat",
            messages=[{"role": "user", "content": "controlled"}],
            stream=True,
            stream_options={"include_usage": True},
        )
        assert (
            "".join(c.choices[0].delta.content or "" for c in stream if c.choices)
            == "answer"
        )
        result = client.embeddings.create(
            model="fixture-embedding", input=["controlled input"]
        )
        assert len(result.data[0].embedding) == 5000

        async def embed():
            result = await async_client.embeddings.create(
                model="fixture-embedding", input=["controlled async"]
            )
            assert len(result.data[0].embedding) == 5000

        asyncio.run(embed())
        return {"dense_dimensions": 5000, "native_stream": "answer"}

    try:
        print(run())
    finally:
        sdk.uninstrument()
        client.close()
        asyncio.run(async_client.close())
        telemetry.shutdown()


if __name__ == "__main__":
    main()
