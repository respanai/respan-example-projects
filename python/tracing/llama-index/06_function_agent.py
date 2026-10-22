"""Run actual function calls through the released FunctionAgent workflow."""

import asyncio

from _shared import build_llm, create_respan, print_result, traced_example
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool


async def main() -> None:
    context = create_respan(
        app_name="llama-index-function-agent", example_name="06_function_agent"
    )

    def multiply_numbers(a: int, b: int) -> int:
        return a * b

    agent = FunctionAgent(
        tools=[FunctionTool.from_defaults(fn=multiply_numbers)],
        llm=build_llm(context.settings),
        streaming=False,
    )
    with traced_example(
        context,
        root_span_name=context.example_name,
        input_data={"query": "multiply 7 by 6"},
    ) as root:
        result = await agent.run(user_msg="Use multiply_numbers for 7 multiplied by 6.")
        root.set_output({"answer": str(result)})
    print_result("Function agent", result)


if __name__ == "__main__":
    asyncio.run(main())
