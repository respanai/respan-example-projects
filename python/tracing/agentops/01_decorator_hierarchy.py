"""AgentOps workflow, agent, task, and tool decorators traced by Respan."""

from __future__ import annotations

from _shared import build_respan, example_scope
from agentops import agent, task, tool, trace


def main() -> None:
    respan = build_respan(
        example_name="decorator-hierarchy",
        workflow_name="agentops_decorator_hierarchy",
    )

    @task(name="prepare_prompt")
    def prepare_prompt(city: str) -> str:
        return f"Look up deterministic weather for {city}."

    @tool(name="lookup_weather")
    def lookup_weather(city: str) -> dict[str, object]:
        return {
            "city": city,
            "condition": "clear",
            "temperature_c": 22,
        }

    @agent(name="weather_agent")
    def weather_agent(city: str) -> dict[str, object]:
        prompt = prepare_prompt(city)
        weather = lookup_weather(city)
        return {"prompt": prompt, "weather": weather}

    @trace(name="agentops_decorator_hierarchy")
    def workflow(city: str) -> dict[str, object]:
        return weather_agent(city)

    with example_scope("decorator-hierarchy"):
        try:
            print(workflow("Tokyo"))
        finally:
            respan.shutdown()


if __name__ == "__main__":
    main()
