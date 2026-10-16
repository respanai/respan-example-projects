"""Instrumentor-level content opt-out retains model and actual usage fields."""

import asyncio

from _fixtures import Fixture
from _shared import build_respan, example_scope
from agentscope.message import UserMsg
from respan import workflow


async def main():
    fixture = Fixture()
    respan = build_respan(
        "capture-opt-out", "agentscope_capture_opt_out", capture_content=False
    )

    @workflow(name="agentscope_capture_opt_out")
    async def run(scenario):
        result = await fixture.model()(
            [UserMsg(name="user", content="private fixture prompt")]
        )
        embedded = await fixture.embedding()(["private fixture document"])
        assert (
            result.content[0].text == "fixture answer"
            and len(embedded.embeddings[0]) == 256
        )
        return {"scenario": scenario, "operations": 2}

    with example_scope("capture-opt-out"):
        try:
            print(await run("content disabled"))
        finally:
            try:
                await fixture.close()
            finally:
                respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
