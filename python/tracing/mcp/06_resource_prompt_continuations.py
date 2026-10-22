"""MCP 2 modern resource and prompt input-required continuations."""

import asyncio

from _shared import create_respan, finish_respan, print_result, workflow_attributes
from mcp import Client
from mcp.server.mcpserver import Context, MCPServer
from mcp.types import InputRequiredResult
from respan import Respan, workflow

WORKFLOW_NAME = "mcp_resource_prompt_continuations"
server = MCPServer("respan-mcp2-resource-input")


@server.resource("text://{item}")
def text_resource(item: str, ctx: Context) -> str | InputRequiredResult:
    if not ctx.request_state:
        return InputRequiredResult(input_requests={}, request_state=item)
    return f"resource {item}"


@server.prompt()
def confirmation(ctx: Context) -> str | InputRequiredResult:
    if not ctx.request_state:
        return InputRequiredResult(input_requests={}, request_state="prompt")
    return "confirmed prompt"


@workflow(name=WORKFLOW_NAME)
async def run_example() -> dict[str, str]:
    async with Client(server, mode="2026-07-28") as client:
        resource = await client.session.read_resource(
            "text://demo", allow_input_required=True
        )
        assert isinstance(resource, InputRequiredResult)
        resource_result = await client.session.read_resource(
            "text://demo", request_state=resource.request_state, input_responses={}
        )
        assert resource_result.contents[0].text == "resource demo"
        prompt = await client.session.get_prompt(
            "confirmation", allow_input_required=True
        )
        assert isinstance(prompt, InputRequiredResult)
        prompt_result = await client.session.get_prompt(
            "confirmation", request_state=prompt.request_state, input_responses={}
        )
        assert prompt_result.messages[0].content.text == "confirmed prompt"
        result = {
            "resource": resource_result.contents[0].text,
            "prompt": prompt_result.messages[0].content.text,
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
