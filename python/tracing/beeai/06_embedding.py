"""Capture released BeeAI embedding APIs, real result vectors, and usage."""

import asyncio

from _shared import create_respan, example_attributes, live_mode
from respan import workflow

WORKFLOW_NAME = "BeeAI Embedding Example"
respan = create_respan("beeai-embedding")
from _fixtures import FixtureEmbeddingModel


@workflow(name=WORKFLOW_NAME)
async def embedding():
    if live_mode():
        from beeai_framework.backend import EmbeddingModel

        model = EmbeddingModel.from_name("openai:text-embedding-3-small")
    else:
        model = FixtureEmbeddingModel()
    output = await model.create(
        ["A trace connects related operations.", "Usage comes from provider fields."]
    )
    assert len(output.embeddings) == 2
    print(f"Embedding dimensions: {[len(vector) for vector in output.embeddings]}")


async def main():
    try:
        with example_attributes(WORKFLOW_NAME):
            await embedding()
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
