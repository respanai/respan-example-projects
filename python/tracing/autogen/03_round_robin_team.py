"""A two-agent team with the native TaskResult and connected hierarchy."""

from _shared import client, response, run
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat


async def scenario():
    first = AssistantAgent(
        "researcher", model_client=await client(response("Fixture research."))
    )
    second = AssistantAgent(
        "reviewer", model_client=await client(response("Fixture review complete."))
    )
    team = RoundRobinGroupChat([first, second], max_turns=2)
    result = await team.run(task="Research and review a fixture.")
    assert result.messages[-1].content == "Fixture review complete."
    state = await team.save_state()
    assert state
    return "Team result and state verified."


if __name__ == "__main__":
    run("round-robin-team", scenario)
