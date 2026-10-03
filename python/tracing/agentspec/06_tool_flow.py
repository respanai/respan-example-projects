"""A real FlowBuilder graph with explicit inputs, outputs and data edges."""

import asyncio

from _shared import build_respan, example_scope
from pyagentspec.adapters.langgraph import AgentSpecLoader
from pyagentspec.flows.flowbuilder import FlowBuilder
from pyagentspec.flows.nodes.toolnode import ToolNode
from pyagentspec.property import FloatProperty
from pyagentspec.tools import ServerTool


def graph():
    tool = ServerTool(
        name="subtract",
        inputs=[FloatProperty(title="left"), FloatProperty(title="right")],
        outputs=[FloatProperty(title="difference")],
    )
    node = ToolNode(name="subtract-node", tool=tool)
    builder = (
        FlowBuilder()
        .add_node(node)
        .set_entry_point(node, inputs=tool.inputs)
        .set_finish_points(node, outputs=tool.outputs)
    )
    for key in ["left", "right"]:
        builder.add_data_edge("StartNode", node, key)
    builder.add_data_edge(node, "EndNode_1", "difference")
    flow = builder.build(name="fixture-flow")
    return AgentSpecLoader(
        tool_registry={"subtract": lambda left, right: left - right}
    ).load_component(flow)


async def main():
    respan = build_respan("tool-flow")
    with example_scope("tool-flow"):
        try:
            sync = graph().invoke({"inputs": {"left": 5.0, "right": 2.0}})
            asynchronous = await graph().ainvoke(
                {"inputs": {"left": 5.0, "right": 2.0}}
            )
            assert sync["outputs"] == {"difference": 3.0}
            assert asynchronous["outputs"] == {"difference": 3.0}
            print({"sync_result": sync, "async_result": asynchronous})
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
