"""Consume the native Strands async event stream."""

import asyncio

from _shared import create_gateway_model, create_respan, finish_respan, new_run_id
from respan import propagate_attributes, workflow
from strands import Agent

WORKFLOW_NAME = "Strands Streaming Example"


def main() -> None:
    run_id = new_run_id("stream")
    respan = create_respan("streaming", run_id)
    try:
        agent = Agent(
            name=WORKFLOW_NAME, model=create_gateway_model(), callback_handler=None
        )

        @workflow(name=WORKFLOW_NAME)
        async def run_workflow(prompt: str) -> dict[str, str]:
            result = None
            async for event in agent.stream_async(prompt):
                result = event.get("result", result)
            assert result is not None
            return {"answer": str(result)}

        with propagate_attributes(
            metadata={"run_id": run_id, "script": "06_streaming.py"}
        ):
            print(asyncio.run(run_workflow("Give one tracing tip.")))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
