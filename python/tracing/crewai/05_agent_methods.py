"""CrewAI's direct Agent kickoff and kickoff_async APIs."""

import asyncio

from _fixtures import FixtureServer
from _shared import create_respan, run_with_attributes, shutdown_respan
from crewai import Agent
from respan import workflow


@workflow(name="crewai_05_agent_methods")
def run_agents(scenario: str) -> dict:
    agent = Agent(
        role="FixtureAgent",
        goal="Answer fixture questions",
        backstory="A deterministic example agent.",
        llm=FixtureServer().llm(),
        verbose=False,
    )
    sync = agent.kickoff("Give a fixture answer.")
    asynchronous = asyncio.run(agent.kickoff_async("Give an async fixture answer."))
    return {"scenario": scenario, "sync": sync.raw, "async": asynchronous.raw}


def main():
    context = create_respan(
        app_name="crewai-05-agent-methods",
        example_name="05_agent_methods",
        workflow_name="crewai_05_agent_methods",
    )
    try:
        print(run_with_attributes(context, lambda: run_agents("standalone-agents")))
    finally:
        shutdown_respan(context)


if __name__ == "__main__":
    main()
