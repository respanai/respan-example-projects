"""Controlled HTTP401 with real SDK errors and no fabricated model response."""

from _shared import client, run
from autogen_agentchat.agents import AssistantAgent
from openai import AuthenticationError


async def scenario():
    agent = AssistantAgent("provider_error", model_client=await client(401))
    try:
        await agent.run(task="Return a controlled provider failure.")
    except AuthenticationError:
        return "Native authentication error preserved."
    raise AssertionError("Expected provider error")


if __name__ == "__main__":
    run("provider-error", scenario)
