"""Released Cohere SDK async tools and controlled failure, using an HTTP fixture."""

import asyncio

import cohere
import httpx
from _shared import create_respan, fixture_response, run_with_example_attributes
from respan import workflow


@workflow(name="cohere_async_tools_and_error.workflow")
async def run():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(fixture_response)
    ) as transport:
        client = cohere.AsyncClientV2(api_key="fixture-key", httpx_client=transport)
        response = await client.chat(
            model="command-a",
            messages=[{"role": "user", "content": "weather"}],
            tools=[
                {
                    "type": "function",
                    "function": {"name": "weather", "parameters": {"type": "object"}},
                }
            ],
        )
        embeddings = await client.embed(
            model="embed-v4.0",
            input_type="search_document",
            inputs=[{"content": [{"type": "text", "text": "async embedding input"}]}],
            embedding_types=["float"],
        )
        assert embeddings.embeddings.float_ == [[0.01, 0.02, 0.03]]
        await client.rerank(
            model="rerank-v3.5",
            query="rank documents",
            documents=["first", "second"],
            top_n=1,
        )
        try:
            await client.chat(
                model="command-a",
                messages=[{"role": "user", "content": "expected failure"}],
            )
        except cohere.BadRequestError:
            return {
                "tool": response.message.tool_calls[0].function.name,
                "expected_error": True,
            }
        raise AssertionError("Expected a provider error")


def main():
    respan = create_respan("cohere-async-tools-example")
    try:
        result = run_with_example_attributes(
            respan,
            workflow_name="cohere_async_tools_and_error.workflow",
            action=lambda: asyncio.run(run()),
        )
        print(result)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
