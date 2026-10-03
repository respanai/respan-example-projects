"""Controlled model failure keeps the SDK exception and error span."""

from _shared import DeterministicLlm, run_agent_once, run_scenario
from google.adk.agents import Agent


async def scenario():
    try:
        await run_agent_once(
            agent=Agent(
                name="failing_agent",
                model=DeterministicLlm(model="fixture-error", fail=True),
            ),
            app_name="06_model_error",
            prompt="Synthetic failure request",
        )
    except RuntimeError as exc:
        assert "Synthetic ADK model failure" in str(exc)
        return {"caught": "RuntimeError"}
    raise AssertionError("Expected fixture failure")


if __name__ == "__main__":
    run_scenario("06_model_error", scenario)
