"""Semantic Kernel chat completion with a fixture transport (or an opt-in gateway call)."""

import asyncio
from pathlib import Path

from _shared import (
    close_kernel_clients,
    create_kernel,
    create_respan,
    example_attributes,
    print_result,
)
from respan import workflow
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments

SCRIPT_NAME = Path(__file__).name
APP_NAME = SCRIPT_NAME.removesuffix(".py")


@workflow(name=SCRIPT_NAME)
async def run_chat_completion(prompt: str) -> str:
    kernel = create_kernel()
    settings = OpenAIChatPromptExecutionSettings(
        service_id="chat",
        temperature=0.2,
        max_tokens=80,
    )
    result = await kernel.invoke_prompt(
        prompt,
        arguments=KernelArguments(settings=settings),
    )
    output = str(result)
    print_result("chat_completion", output)
    return output


async def main() -> None:
    respan = create_respan(APP_NAME)
    try:
        with example_attributes(APP_NAME):
            await run_chat_completion(
                "Reply in one sentence: what does Semantic Kernel help developers build?"
            )
    finally:
        try:
            await close_kernel_clients()
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
