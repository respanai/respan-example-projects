"""Trace a smolagents CodeAgent run with a local tool."""

from _shared import build_model, build_respan, example_attributes
from respan import workflow
from smolagents import CodeAgent, tool

EXAMPLE_NAME = "code-agent"
WORKFLOW_NAME = "smolagents_code_agent_workflow"


@tool
def get_city_population(city: str) -> str:
    """Return a small population fact for a city.

    Args:
        city: City name to look up.
    """
    populations = {
        "paris": "Paris has about 2.1 million residents in the city proper.",
        "tokyo": "Tokyo has about 14 million residents in the prefecture.",
        "new york": "New York City has about 8.3 million residents.",
    }
    return populations.get(city.lower(), f"No population fact is stored for {city}.")


@workflow(name=WORKFLOW_NAME)
def execute_code_agent_workflow(prompt: str) -> str:
    agent = CodeAgent(
        tools=[get_city_population],
        model=build_model("code"),
        max_steps=3,
        verbosity_level=0,
    )
    result = agent.run(prompt)
    print(result)
    return str(result)


def run_code_agent() -> str:
    respan = build_respan(example_name=EXAMPLE_NAME, workflow_name=WORKFLOW_NAME)
    try:
        with example_attributes(EXAMPLE_NAME, WORKFLOW_NAME):
            return execute_code_agent_workflow(
                "Use the get_city_population tool for Paris exactly once, then return "
                "one sentence with the population fact."
            )
    finally:
        respan.shutdown()


if __name__ == "__main__":
    run_code_agent()
