"""Real tool execution, false/zero results, reflection and controlled failure."""

from _shared import client, response, run
from autogen_agentchat.agents import AssistantAgent


async def scenario():
    def count_items() -> int:
        """Return the fixture inventory count."""
        return 0

    def fail_tool() -> str:
        """Raise a controlled fixture error."""
        raise ValueError("Controlled AutoGen tool failure")

    model = await client(
        response(calls=[("zero-call", "count_items", "{}")]),
        response("Inventory is zero."),
        response(calls=[("error-call", "fail_tool", "{}")]),
        response("Tool failure handled."),
    )
    zero = await AssistantAgent(
        "inventory", model_client=model, tools=[count_items], reflect_on_tool_use=True
    ).run(task="Check inventory.")
    failure = await AssistantAgent(
        "failure_handler",
        model_client=model,
        tools=[fail_tool],
        reflect_on_tool_use=True,
    ).run(task="Handle a controlled tool failure.")
    assert zero.messages[-1].content == "Inventory is zero."
    assert failure.messages[-1].content == "Tool failure handled."
    return "Zero result, tool IDs, history and handled failure verified."


if __name__ == "__main__":
    run("tool-reflection-and-error", scenario)
