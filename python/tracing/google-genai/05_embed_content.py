from __future__ import annotations

import asyncio
import os

from _shared import (
    example_attributes,
    make_client,
    make_respan,
    print_result,
    workflow_name,
)
from google.genai import types
from respan import workflow

EXAMPLE_NAME = "embed-content"


@workflow(name=workflow_name(EXAMPLE_NAME))
async def embed_content() -> list[list[float]]:
    client = make_client()
    model = os.getenv("RESPAN_GOOGLE_EMBEDDING_MODEL", "gemini-embedding-001")
    try:
        sync_result = client.models.embed_content(
            model=model, contents=["alpha", "beta"], config={"output_dimensionality": 3}
        )
        async_result = await client.aio.models.embed_content(
            model=model, contents="async text", config={"output_dimensionality": 3}
        )
        vectors = [
            embedding.values
            for embedding in [*sync_result.embeddings, *async_result.embeddings]
        ]
        assert len(vectors) == 3 and all(len(vector) == 3 for vector in vectors)
        if os.getenv("RESPAN_GOOGLE_GENAI_MODE") == "fixture":
            from _fixtures import make_fixture_client

            multimodal = client.models.embed_content(
                model="gemini-embedding-2-preview",
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(text="image"),
                            types.Part(
                                file_data=types.FileData(
                                    file_uri="gs://fixture/image.jpg",
                                    mime_type="image/jpeg",
                                )
                            ),
                        ],
                    )
                ],
            )
            assert multimodal.embeddings[0].values == [0.25, 0.5, 0.75]
            vertex = make_fixture_client(vertex=True)
            try:
                with_usage = await vertex.aio.models.embed_content(
                    model="text-embedding-005", contents=["alpha", "beta"]
                )
                assert (
                    sum(item.statistics.token_count for item in with_usage.embeddings)
                    == 6
                )
            finally:
                await vertex.aio.aclose()
                vertex.close()
        return vectors
    finally:
        await client.aio.aclose()
        client.close()


def main() -> None:
    respan = make_respan(EXAMPLE_NAME)
    try:
        with example_attributes(EXAMPLE_NAME) as identifier:
            result = asyncio.run(embed_content())
            print_result(
                EXAMPLE_NAME, identifier, f"Captured {len(result)} embedding vectors."
            )
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
