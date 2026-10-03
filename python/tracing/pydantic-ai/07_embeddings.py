"""Native sync/async embeddings and a controlled local model failure."""

import asyncio

from _gateway import finish_respan, make_respan
from pydantic_ai import Embedder
from pydantic_ai.embeddings.test import TestEmbeddingModel
from respan import workflow


class FailingModel(TestEmbeddingModel):
    async def embed(self, *args, **kwargs):
        raise RuntimeError("expected embedding model failure")


@workflow(name="pydantic_ai_embeddings")
def run_embeddings():
    embedder = Embedder(TestEmbeddingModel(dimensions=128))
    query = embedder.embed_query_sync("Find tracing documentation")
    documents = asyncio.run(
        embedder.embed_documents(
            ["Tracing preserves context", "Embeddings enable search"]
        )
    )
    assert len(query.embeddings[0]) == 128
    assert len(documents.embeddings) == 2
    try:
        Embedder(FailingModel()).embed_query_sync("controlled embedding failure")
    except RuntimeError as error:
        assert str(error) == "expected embedding model failure"
    else:
        raise AssertionError("Expected the local model failure")
    return {
        "query_vectors": 1,
        "document_vectors": 2,
        "dimensions": 128,
        "expected_error": True,
    }


def main():
    respan = None
    try:
        respan = make_respan("embeddings")
        print(run_embeddings())
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
