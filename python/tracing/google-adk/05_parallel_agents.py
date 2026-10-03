"""Parallel agents retain separate model spans under their shared runner."""

from _shared import DeterministicLlm, run_agent_once, run_scenario
from google.adk.agents import Agent, ParallelAgent


async def scenario():
    agents = [
        Agent(name=name, model=DeterministicLlm(model="fixture-adk"))
        for name in ("left", "right")
    ]
    return await run_agent_once(
        agent=ParallelAgent(name="parallel", sub_agents=agents),
        app_name="05_parallel_agents",
        prompt="Synthetic parallel request",
    )


if __name__ == "__main__":
    run_scenario("05_parallel_agents", scenario)
