import asyncio

from _shared import (
    create_respan,
    finish_respan,
    print_result,
    with_session,
    workflow_attributes,
)
from respan import Respan, workflow

WORKFLOW_NAME = "mcp_resource_read_workflow"


@workflow(name=WORKFLOW_NAME)
async def run_resource_read_example() -> dict[str, object]:
    async with with_session() as session:
        resources = await session.list_resources()
        templates = await session.list_resource_templates()
        assert templates.resource_templates
        result = await session.read_resource("profile://city/paris")
        output = {
            "available_resources": [
                str(resource.uri) for resource in resources.resources
            ],
            "resource_uri": "profile://city/paris",
            "result": result.contents[0].text,
        }
        print_result(WORKFLOW_NAME, output)
        return output


async def main() -> None:
    respan = create_respan(WORKFLOW_NAME)
    try:
        with Respan.propagate_attributes(**workflow_attributes(WORKFLOW_NAME)):
            await run_resource_read_example()
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
