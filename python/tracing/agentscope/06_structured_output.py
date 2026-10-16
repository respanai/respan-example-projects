"""AgentScope structured generation through the real OpenAI model parser."""

import asyncio

from _fixtures import Fixture
from _shared import build_respan, example_scope
from agentscope.message import UserMsg
from respan import workflow


async def main():
    fixture = Fixture()
    respan = build_respan("structured-output", "agentscope_structured_output")

    @workflow(name="agentscope_structured_output")
    async def run(prompt):
        response = await fixture.model().generate_structured_output(
            [UserMsg(name="user", content=prompt)],
            {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
            },
        )
        assert response.content == {"answer": "fixture value"}
        assert response.usage.input_tokens == 0
        return response.content

    with example_scope("structured-output"):
        try:
            print(await run("Return a structured fixture value"))
        finally:
            try:
                await fixture.close()
            finally:
                respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
