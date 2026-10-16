"""CrewAI tool-use example with Respan tracing."""

from _shared import (
    build_llm,
    create_respan,
    print_result,
    result_text,
    run_with_attributes,
    shutdown_respan,
)

WORKFLOW_NAME = "crewai_02_tool_use"


def lookup_city_weather(city: str) -> str:
    """Look up deterministic weather for a city."""
    weather = {
        "Paris": "Sunny, 22C",
        "Tokyo": "Cloudy, 18C",
        "New York": "Clear, 20C",
    }
    return weather.get(city, "Mild, 21C")


def lookup_city_population(city: str) -> str:
    """Look up deterministic population data for a city."""
    populations = {
        "Paris": "about 2.1 million people",
        "Tokyo": "about 14 million people",
        "New York": "about 8.3 million people",
    }
    return populations.get(city, "unknown population")


def run_tool_crew(context) -> str:
    from crewai import Agent, Crew, Process, Task
    from crewai.tools import tool

    weather_tool = tool("lookup_city_weather")(lookup_city_weather)
    population_tool = tool("lookup_city_population")(lookup_city_population)
    llm = build_llm(context.settings)

    researcher = Agent(
        role="City Researcher",
        goal="Use tools to gather city facts before answering",
        backstory="You collect factual city details using available tools.",
        tools=[weather_tool, population_tool],
        llm=llm,
        verbose=False,
    )
    task = Task(
        name="Research Paris",
        description=(
            "Research the weather and population for Paris, then summarize the "
            "result in two short bullets. Use the provided tools."
        ),
        expected_output="Two short bullets with weather and population details.",
        agent=researcher,
    )
    crew = Crew(
        name=WORKFLOW_NAME,
        agents=[researcher],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
    return result_text(crew.kickoff())


def main() -> None:
    context = create_respan(
        app_name="crewai-02-tool-use",
        example_name="02_tool_use",
        workflow_name=WORKFLOW_NAME,
    )
    try:
        output = run_with_attributes(context, lambda: run_tool_crew(context))
        print_result("Crew output", output)
        print_result("Workflow name", WORKFLOW_NAME)
        print_result("Example run id", context.run_id)
    finally:
        shutdown_respan(context)


if __name__ == "__main__":
    main()
