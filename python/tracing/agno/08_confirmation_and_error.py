"""Confirm a synthetic tool locally, resume the run, and record a fixture error."""

import asyncio

from _fixture_model import model
from _shared import create_respan, example_attributes, print_result
from agno.agent import Agent
from agno.exceptions import ModelProviderError
from agno.tools import tool
from respan import workflow


@tool(requires_confirmation=True)
def weather(city: str) -> str:
    """Return synthetic weather; no external service call."""
    return f"Sunny in {city}"


@workflow(name="agno_08_confirmation_and_error")
async def run_confirmation():
    agent = Agent(name="Confirmation", model=model(), tools=[weather], telemetry=False)
    paused = await agent.arun("weather")
    for requirement in paused.requirements:
        requirement.confirm()
    completed = await agent.acontinue_run(run_response=paused)
    failed = Agent(name="Expected Error", model=model(), telemetry=False)
    try:
        error_output = await failed.arun("expected failure")
        if (
            "error"
            in str(getattr(error_output.status, "value", error_output.status)).lower()
        ):
            return {
                "resumed": completed.content,
                "expected_error": error_output.content,
            }
    except ModelProviderError as error:
        return {"resumed": completed.content, "expected_error": type(error).__name__}
    raise AssertionError("Expected the fixture provider error")


def main():
    respan, _ = create_respan(app_name="agno-08-confirmation-error")
    try:
        with example_attributes(respan, "agno_08_confirmation_and_error"):
            result = asyncio.run(run_confirmation())
        print_result("Result", result)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
