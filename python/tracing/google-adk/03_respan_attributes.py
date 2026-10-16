"""Google ADK run with Respan customer, thread, and metadata attributes."""

import asyncio
from pathlib import Path

from _shared import (
    create_gateway_model,
    create_respan,
    example_attributes,
    example_run_id,
    run_agent_once,
)
from google.adk.agents import Agent
from respan import propagate_attributes, workflow

SCRIPT_NAME = Path(__file__).name
APP_NAME = SCRIPT_NAME.removesuffix(".py")


@workflow(name=SCRIPT_NAME)
async def run_respan_attributes(prompt: str) -> str:
    agent = Agent(
        name="attribute_agent",
        model=create_gateway_model(),
        instruction="You answer in one concise sentence.",
    )
    output = await run_agent_once(
        agent=agent,
        app_name=APP_NAME,
        prompt=prompt,
    )
    print(output)
    return output


async def main() -> None:
    respan = create_respan(APP_NAME)
    try:
        with (
            example_attributes(APP_NAME),
            propagate_attributes(
                customer_identifier="google-adk-example-user",
                thread_identifier=f"{example_run_id()}:{APP_NAME}",
                metadata={
                    "integration": "google-adk",
                    "example": APP_NAME,
                    "run_id": example_run_id(),
                    "scenario": "attributes",
                },
            ),
        ):
            await run_respan_attributes("Explain why trace attributes are useful.")
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
