"""New ModelConsultTool success and adviser failure with real response usage."""

from _shared import DeterministicLlm, run_agent_once, run_scenario
from google.adk.agents import Agent
from google.adk.tools.model_consult import ModelConsultTool


async def scenario():
    outputs = []
    for fail in (False, True):
        advisor = DeterministicLlm(model="fixture-advisor", fail=fail)
        tool = ModelConsultTool(model=advisor, thinking_level=None, max_uses=1)
        agent = Agent(
            name="executor",
            model=DeterministicLlm(model="fixture-executor"),
            tools=[tool],
        )
        outputs.append(
            await run_agent_once(
                agent=agent,
                app_name="09_model_consult",
                prompt="Consult the synthetic advisor",
            )
        )
    return {"runs": len(outputs)}


if __name__ == "__main__":
    run_scenario("09_model_consult", scenario)
