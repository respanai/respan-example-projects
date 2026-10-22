"""Embedding batches, complete vectors, actual usage, and an HTTP failure."""

import asyncio
from pathlib import Path

from _shared import (
    close_kernel_clients,
    create_client,
    create_respan,
    example_attributes,
)
from respan import workflow
from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException

SCRIPT_NAME = Path(__file__).name
APP_NAME = SCRIPT_NAME.removesuffix(".py")


@workflow(name=SCRIPT_NAME)
async def run_embeddings(documents: list[str]) -> dict:
    service = OpenAITextEmbedding(
        ai_model_id="fixture-embedding", async_client=create_client()
    )
    result = await service.generate_embeddings(documents, batch_size=2)
    assert result.shape == (3, 128) and result[2, 127] == 127
    try:
        await service.generate_raw_embeddings(["fixture-failure"])
    except ServiceResponseException as exc:
        assert "failed to generate embeddings" in str(exc)
        error = type(exc).__name__
    else:
        raise AssertionError("Expected the controlled HTTP failure")
    return {
        "shape": list(result.shape),
        "last_value": float(result[2, 127]),
        "expected_error": error,
    }


async def main():
    respan = create_respan(APP_NAME)
    try:
        with example_attributes(APP_NAME):
            print(
                await run_embeddings(
                    ["first fixture", "second fixture", "third fixture"]
                )
            )
    finally:
        try:
            await close_kernel_clients()
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
