"""Use AsyncGuard for local parsing and a deterministic custom LLM callback."""

import asyncio

from _shared import example_attributes, local_guard, make_respan, result_summary
from guardrails import AsyncGuard
from pydantic import BaseModel
from respan import workflow

WORKFLOW_NAME = "guardrails_async_workflow"


class Reply(BaseModel):
    answer: str


async def generate(*, messages, **kwargs):
    return '{"answer":"Async fixture reply"}'


@workflow(name=WORKFLOW_NAME)
async def run_example():
    guard = local_guard(AsyncGuard.for_pydantic(Reply))
    parsed = await guard.parse('{"answer":"Async parsed reply"}', num_reasks=0)
    result = await guard(
        llm_api=generate,
        messages=[{"role": "user", "content": "Return an async fixture reply"}],
        num_reasks=0,
    )
    assert parsed.validation_passed and result.validation_passed
    return {"parse": result_summary(parsed), "generation": result_summary(result)}


async def main():
    respan, _ = make_respan(WORKFLOW_NAME)
    try:
        with example_attributes("async-validation", WORKFLOW_NAME):
            print(await run_example())
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
