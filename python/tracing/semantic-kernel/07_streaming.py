"""Streaming text with zero usage, empty SSE, and controlled chat failure."""

import asyncio
from pathlib import Path

from _shared import (
    close_kernel_clients,
    create_client,
    create_respan,
    example_attributes,
)
from respan import workflow
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException

SCRIPT_NAME = Path(__file__).name
APP_NAME = SCRIPT_NAME.removesuffix(".py")


@workflow(name=SCRIPT_NAME)
async def run_streaming(prompt: str) -> dict:
    service = OpenAIChatCompletion(
        ai_model_id="fixture-model", async_client=create_client()
    )
    results = []
    for question in (prompt, "empty-stream"):
        history = ChatHistory()
        history.add_user_message(question)
        chunks = [
            chunk
            async for chunk in service.get_streaming_chat_message_contents(
                history, OpenAIChatPromptExecutionSettings()
            )
        ]
        results.append("".join(str(message) for chunk in chunks for message in chunk))
    assert results == ["fixture stream", ""]
    history = ChatHistory()
    history.add_user_message("fixture-failure")
    try:
        await service.get_chat_message_contents(
            history, OpenAIChatPromptExecutionSettings()
        )
    except ServiceResponseException as exc:
        assert "controlled fixture failure" in str(exc)
        error = type(exc).__name__
    else:
        raise AssertionError("Expected controlled chat HTTP failure")
    return {"streams": results, "expected_error": error}


async def main():
    respan = create_respan(APP_NAME)
    try:
        with example_attributes(APP_NAME):
            print(await run_streaming("Stream a fixture answer."))
    finally:
        try:
            await close_kernel_clients()
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
