"""Instrumentor-level capture_content=False retains non-content telemetry."""

import asyncio
from pathlib import Path

from _shared import (
    close_kernel_clients,
    create_client,
    create_respan,
    example_attributes,
)
from respan import workflow
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAITextEmbedding,
)

SCRIPT_NAME = Path(__file__).name
APP_NAME = SCRIPT_NAME.removesuffix(".py")


@workflow(name=SCRIPT_NAME)
async def run_capture_opt_out(scenario: str) -> dict:
    client = create_client()
    agent = ChatCompletionAgent(
        service=OpenAIChatCompletion(ai_model_id="fixture-model", async_client=client),
        name="PrivateCaptureAgent",
    )
    await agent.get_response(messages="private-capture-prompt")
    result = await OpenAITextEmbedding(
        ai_model_id="fixture-embedding", async_client=client
    ).generate_embeddings(["private-capture-document"])
    assert result.shape == (1, 128)
    return {"scenario": scenario, "shape": list(result.shape)}


async def main():
    respan = create_respan(APP_NAME, capture_content=False)
    try:
        with example_attributes(APP_NAME):
            print(await run_capture_opt_out("instrumentor-content-opt-out"))
    finally:
        try:
            await close_kernel_clients()
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
