import asyncio

from _fixtures import NativeRuntime
from _shared import create_respan, example_context, finish_respan
from respan import workflow
from vertexai.language_models import TextEmbeddingInput


async def main():
    native = NativeRuntime()
    respan = create_respan()
    model, channel = await native.async_embedding()

    @workflow(name="vertexai_embeddings")
    async def embed(text):
        inputs = [TextEmbeddingInput(text, task_type="RETRIEVAL_DOCUMENT")]
        sync = native.embedding().get_embeddings(inputs)
        asynchronous = await model.get_embeddings_async(inputs)
        assert len(sync[0].values) == len(asynchronous[0].values) == 5001
        assert (
            sync[0].statistics.token_count
            == asynchronous[0].statistics.token_count
            == 5
        )
        return {
            "dimensions": len(sync[0].values),
            "source_tokens": sync[0].statistics.token_count,
        }

    try:
        with example_context("embeddings"):
            assert (await embed("native embedding"))["dimensions"] == 5001
        print("embeddings: sync/async complete 5001 vectors and source statistics")
    finally:
        await channel.close()
        native.close()
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
