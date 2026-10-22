"""The latest AgentTool API retains the nested agent and tool parentage."""

from _shared import client, response, run
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool


async def scenario():
    worker = AssistantAgent(
        "worker", model_client=await client(response("Worker fixture answer."))
    )
    model = await client(
        response(calls=[("nested-call", "worker", '{"task":"Worker fixture task."}')]),
        response("Delegation complete."),
    )
    parent = AssistantAgent(
        "coordinator",
        model_client=model,
        tools=[AgentTool(worker, return_value_as_last_message=True)],
        reflect_on_tool_use=True,
    )
    result = await parent.run(task="Delegate to the worker.")
    assert result.messages[-1].content == "Delegation complete."
    return "Nested agent-as-tool verified."


if __name__ == "__main__":
    run("agent-as-tool", scenario)
