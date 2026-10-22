"""Native context Model methods and four real Toolkit execution variants."""

from __future__ import annotations

import asyncio
import json

from _controlled import async_vector_tool, model, vector_tool
from _shared import create_respan, finish_respan, workflow_attributes
from mirascope import llm
from respan import workflow


@workflow(name="mirascope-native-context-surfaces")
async def run():
    native, _ = model()
    ctx = llm.Context(deps={})
    assert native.context_call("context call", ctx=ctx).text() == "native result"
    assert (
        await native.context_call_async("async context call", ctx=ctx)
    ).text() == "native result"
    assert "native stream" in "".join(
        native.context_stream("context stream", ctx=ctx).text_stream()
    )
    stream = await native.context_stream_async("async context stream", ctx=ctx)
    assert "native stream" in "".join([part async for part in stream.text_stream()])
    for owner in ("Toolkit", "ContextToolkit", "AsyncToolkit", "AsyncContextToolkit"):
        tool = async_vector_tool if owner.startswith("Async") else vector_tool
        call = llm.ToolCall(
            id=f"native-{owner}", name=tool.name, args='{"values":[0,1,2]}'
        )
        args = [ctx, call] if "Context" in owner else [call]
        output = getattr(llm, owner)([tool]).execute(*args)
        if owner.startswith("Async"):
            output = await output
        assert output.error is None and output.id == call.id
    return {"context_model_methods": 4, "native_toolkits": 4}


async def main():
    runtime = create_respan("mirascope-native-context-surfaces")
    try:
        with runtime.propagate_attributes(
            **workflow_attributes("mirascope-native-context-surfaces", __file__)
        ):
            print(json.dumps(await run()))
    finally:
        finish_respan(runtime)


if __name__ == "__main__":
    asyncio.run(main())
