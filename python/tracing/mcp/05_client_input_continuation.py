"""MCP 2 client, input-required continuation, and protocol tool-error results."""

import asyncio

from _shared import create_respan, finish_respan, print_result, workflow_attributes
from mcp import Client
from mcp.server.mcpserver import Context, MCPServer
from mcp.types import InputRequiredResult
from respan import Respan, workflow

WORKFLOW_NAME = "mcp_input_continuation_workflow"
server = MCPServer("respan-mcp2-local")


@server.tool()
def confirm(ctx: Context) -> str | InputRequiredResult:
    if not ctx.request_state:
        return InputRequiredResult(input_requests={}, request_state="confirm-next-call")
    return "confirmed"


@server.tool()
def controlled_failure() -> str:
    raise ValueError("Deterministic MCP tool failure")


@workflow(name=WORKFLOW_NAME)
async def run_example() -> dict[str, object]:
    async with Client(server, mode="2026-07-28") as client:
        pending = await client.session.call_tool("confirm", allow_input_required=True)
        assert isinstance(pending, InputRequiredResult)
        completed = await client.session.call_tool(
            "confirm", input_responses={}, request_state=pending.request_state
        )
        assert completed.content[0].text == "confirmed"
        failed = await client.call_tool("controlled_failure")
        assert failed.is_error
        result = {
            "continuation": completed.content[0].text,
            "controlled_tool_error": failed.is_error,
        }
        print_result(WORKFLOW_NAME, result)
        return result


async def main() -> None:
    respan = create_respan(WORKFLOW_NAME)
    try:
        with Respan.propagate_attributes(**workflow_attributes(WORKFLOW_NAME)):
            await run_example()
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
