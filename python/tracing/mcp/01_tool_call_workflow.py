import asyncio

from _shared import (
    create_respan,
    finish_respan,
    print_result,
    with_session,
    workflow_attributes,
)
from opentelemetry import trace
from respan import Respan, workflow

WORKFLOW_NAME = "mcp_tool_call_workflow"


@workflow(name=WORKFLOW_NAME)
async def run_tool_call_example() -> dict[str, object]:
    async with with_session() as session:
        tools = await session.list_tools()
        result = await session.call_tool(
            "summarize_city",
            arguments={"city": "Paris"},
        )
        server_context = await session.call_tool("current_trace_id")
        expected_trace = f"{trace.get_current_span().get_span_context().trace_id:032x}"
        assert server_context.content[0].text == expected_trace
        output = {
            "context_propagated": True,
            "available_tools": [tool.name for tool in tools.tools],
            "called_tool": "summarize_city",
            "result": result.content[0].text,
        }
        print_result(WORKFLOW_NAME, output)
        return output


async def main() -> None:
    respan = create_respan(WORKFLOW_NAME)
    try:
        with Respan.propagate_attributes(**workflow_attributes(WORKFLOW_NAME)):
            await run_tool_call_example()
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
