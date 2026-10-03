"""Real Cohere async SSE parsing: completion, disconnect, and early close."""

import asyncio

import cohere
import httpx
from _shared import create_respan, fixture_response, run_with_example_attributes
from respan import workflow


class DisconnectedBody(httpx.AsyncByteStream):
    async def __aiter__(self):
        yield b'data: {"type":"message-start","id":"disconnect","delta":{"message":{"role":"assistant","content":[],"tool_calls":[]}}}\n\n'
        raise httpx.ReadError("expected example stream disconnect")


def response(request: httpx.Request) -> httpx.Response:
    if b"disconnect" in request.content:
        return httpx.Response(
            200,
            stream=DisconnectedBody(),
            headers={"content-type": "text/event-stream"},
        )
    return fixture_response(request)


@workflow(name="cohere_async_streaming.workflow")
async def run() -> dict[str, object]:
    async with httpx.AsyncClient(transport=httpx.MockTransport(response)) as transport:
        client = cohere.AsyncClientV2(api_key="fixture-key", httpx_client=transport)
        chunks = []
        async for event in client.chat_stream(
            model="command-a",
            messages=[{"role": "user", "content": "complete the stream"}],
        ):
            if event.type == "content-delta":
                chunks.append(event.delta.message.content.text)
        assert "".join(chunks) == "Stubbed Cohere stream."
        try:
            async for _event in client.chat_stream(
                model="command-a", messages=[{"role": "user", "content": "disconnect"}]
            ):
                pass
        except httpx.ReadError as error:
            assert str(error) == "expected example stream disconnect"
        else:
            raise AssertionError("Expected a stream disconnect")
        stream = client.chat_stream(
            model="command-a", messages=[{"role": "user", "content": "close early"}]
        )
        await anext(stream)
        await stream.aclose()
        return {
            "answer": "".join(chunks),
            "expected_disconnect": True,
            "closed_early": True,
        }


def main() -> None:
    respan = create_respan("cohere-async-streaming-example")
    try:
        print(
            run_with_example_attributes(
                respan,
                workflow_name="cohere_async_streaming.workflow",
                action=lambda: asyncio.run(run()),
            )
        )
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
