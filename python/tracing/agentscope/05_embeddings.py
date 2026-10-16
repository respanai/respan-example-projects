"""Real embedding batching, full vectors and a controlled provider error."""

import asyncio

from _fixtures import Fixture
from _shared import build_respan, example_scope
from agentscope.message import TextBlock
from openai import BadRequestError
from respan import workflow


async def main():
    fixture = Fixture()
    respan = build_respan("embeddings", "agentscope_embeddings")

    @workflow(name="agentscope_embeddings")
    async def run(documents):
        model = fixture.embedding()
        result = await model(documents)
        assert len(result.embeddings) == 3 and all(
            len(v) == 256 for v in result.embeddings
        )
        assert result.embeddings[-1][-1] == 255
        try:
            await model(["fixture-failure"])
        except BadRequestError as exc:
            assert "controlled fixture error" in str(exc)
        else:
            raise AssertionError("Expected controlled provider failure")
        return {"vectors": len(result.embeddings), "dimensions": 256, "last_value": 255}

    with example_scope("embeddings"):
        try:
            print(
                await run(
                    [
                        "first document",
                        TextBlock(text="second document"),
                        "third document",
                    ]
                )
            )
        finally:
            try:
                await fixture.close()
            finally:
                respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
