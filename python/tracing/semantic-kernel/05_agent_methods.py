"""Real ChatCompletionAgent get_response, invoke, and invoke_stream methods."""

import asyncio
from pathlib import Path

from _shared import (
    close_kernel_clients,
    create_client,
    create_respan,
    example_attributes,
)
from respan import workflow
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function

SCRIPT_NAME = Path(__file__).name
APP_NAME = SCRIPT_NAME.removesuffix(".py")


class TravelPlugin:
    @kernel_function(name="get_weather", description="Return fixture weather.")
    def get_weather(self, city: str) -> str:
        return f"{city}: clear, 22 C."


@workflow(name=SCRIPT_NAME)
async def run_agent_methods(question: str) -> dict:
    service = OpenAIChatCompletion(
        ai_model_id="fixture-model", async_client=create_client()
    )
    kernel = Kernel()
    kernel.add_plugin(TravelPlugin(), plugin_name="Travel")
    agent = ChatCompletionAgent(
        service=service,
        kernel=kernel,
        name="TravelAgent",
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    result = await agent.get_response(messages=question)
    assert str(result.message) == "fixture answer"
    invoke = ChatCompletionAgent(service=service, name="InvokeAgent")
    invoked = [
        str(item.message)
        async for item in invoke.invoke(messages="Return a fixture answer.")
    ]
    stream = ChatCompletionAgent(service=service, name="StreamingAgent")
    streamed = [
        str(item.message)
        async for item in stream.invoke_stream(messages="Stream a fixture answer.")
    ]
    assert invoked == ["fixture answer"]
    assert "".join(streamed) == "fixture stream"
    return {
        "answer": str(result.message),
        "invoke": invoked,
        "stream": "".join(streamed),
    }


async def main():
    respan = create_respan(APP_NAME)
    try:
        with example_attributes(APP_NAME):
            print(await run_agent_methods("Use the Travel tool for Tokyo weather."))
    finally:
        try:
            await close_kernel_clients()
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
