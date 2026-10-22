"""Run a BeeAI RequirementAgent with Respan tracing."""

import asyncio

from _shared import create_respan, example_attributes, get_chat_model
from respan import workflow

WORKFLOW_NAME = "BeeAI Requirement Agent Example"
respan = create_respan("beeai-requirement-agent")

from beeai_framework.agents.requirement import RequirementAgent


@workflow(name=WORKFLOW_NAME)
async def run_requirement_agent() -> str:
    agent = RequirementAgent(
        llm=get_chat_model(mode="agent"),
        role="observability assistant",
        instructions=(
            "Answer in one concise paragraph. Focus on practical agent "
            "observability signals."
        ),
    )
    response = await agent.run(
        "Explain why tracing is useful when debugging agent workflows."
    )
    return response.last_message.text


async def main() -> None:
    try:
        with example_attributes(WORKFLOW_NAME) as run_id:
            output = await run_requirement_agent()
            print(f"Run ID: {run_id}")
            print(f"Agent output: {output}")
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
