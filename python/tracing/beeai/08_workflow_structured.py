"""Run a BeeAI Workflow with structured model output under the same tree."""

import asyncio
import json

from _shared import create_respan, example_attributes, get_chat_model
from pydantic import BaseModel
from respan import workflow

WORKFLOW_NAME = "BeeAI Workflow Structured Example"
respan = create_respan("beeai-workflow")
from beeai_framework.backend import UserMessage
from beeai_framework.workflows import Workflow


class State(BaseModel):
    checks: list[str] = []


@workflow(name=WORKFLOW_NAME)
async def structured():
    flow = Workflow(State, name="TraceChecks")

    async def generate(state):
        response = await get_chat_model(mode="structured").run(
            [UserMessage("Return JSON with a checks array.")],
            response_format={"type": "json_object"},
        )
        state.checks = json.loads(response.get_text_content())["checks"]
        return Workflow.END

    flow.add_step("generate", generate)
    result = await flow.run(State())
    assert result.state.checks
    print(result.state.checks)


async def main():
    try:
        with example_attributes(WORKFLOW_NAME):
            await structured()
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
