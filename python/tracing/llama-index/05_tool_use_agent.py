"""Agent tool use: run a LlamaIndex ReAct agent with a FunctionTool."""

import asyncio

from _shared import build_llm, create_respan, print_result, traced_example
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.tools import FunctionTool


async def run_tool_use_agent() -> None:
    context = create_respan(
        app_name="llama-index-05-react-agent-tool",
        example_name="05_react_agent_tool",
    )

    def multiply_numbers(a: int, b: int) -> int:
        return a * b

    multiply_tool = FunctionTool.from_defaults(
        fn=multiply_numbers,
        name="multiply_numbers",
        description="Multiply two integers and return the product.",
    )
    agent = ReActAgent(
        tools=[multiply_tool],
        llm=build_llm(settings=context.settings),
        system_prompt="Use tools when arithmetic is required.",
        streaming=False,
    )

    with traced_example(context):
        response = await agent.run(
            user_msg="Use the multiply_numbers tool to calculate 7 multiplied by 6."
        )

    print_result("Agent answer", response)
    print_result("Example run id", context.run_id)


if __name__ == "__main__":
    asyncio.run(run_tool_use_agent())
