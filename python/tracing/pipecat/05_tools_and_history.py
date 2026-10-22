import asyncio

from _pipeline import run
from _shared import attributes, create_respan, finish_respan, marker, print_result
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from respan import workflow


async def main():
    run_id = marker()
    sdk = create_respan("tools-and-history", run_id)

    @workflow(name="pipecat_tools_and_history")
    async def scenario():
        props = {"field" + str(n): {"type": "string"} for n in range(120)}
        props["api_key"] = {"type": "string", "default": "synthetic secret"}
        tools = ToolsSchema(
            standard_tools=[
                FunctionSchema(
                    name="vector_tool",
                    description="Return dense/sparse fixture vectors.",
                    properties=props,
                    required=[],
                )
            ]
        )
        history = [{"role": "user", "content": "History " + str(n)} for n in range(150)]
        collector, _worker = await run(tool=True, messages=history, tools=tools)
        result = next(
            f for f in collector.frames if type(f).__name__ == "FunctionCallResultFrame"
        )
        return {
            "call_id": result.tool_call_id,
            "dense_dimensions": len(result.result["dense"]),
            "sparse_dimensions": len(result.result["sparse"]),
            "native_argument_values": len(result.arguments["values"]),
        }

    try:
        with attributes("tools-and-history", run_id):
            result = await scenario()
        print_result("tools-and-history", result, run_id)
    finally:
        finish_respan(sdk)


if __name__ == "__main__":
    asyncio.run(main())
