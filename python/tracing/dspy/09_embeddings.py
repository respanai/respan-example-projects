"""Complete callable Embedder vectors; no provider token usage is invented."""

import asyncio

import dspy
from _shared import managed_example, traced_example


def vectors(texts):
    return [[float(i) / 5000 for i in range(5000)] for _ in texts]


async def main():
    with managed_example(
        app_name="dspy-09-embeddings", example_name="09_embeddings"
    ) as context:
        with traced_example(context):
            embedder = dspy.Embedder(vectors, caching=False)
            assert embedder(["first", "second"]).shape == (2, 5000)
            assert (await embedder.acall(["async"])).shape == (1, 5000)
        print("Complete 5000-dimensional sync and async vectors verified")


if __name__ == "__main__":
    asyncio.run(main())
