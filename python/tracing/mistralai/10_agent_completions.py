from __future__ import annotations

import asyncio
import json

from _shared import (
    deterministic_chat_response,
    deterministic_stream_response,
    example_attributes,
    finish_respan,
    make_custom_identifier,
    make_mock_async_client,
    make_mock_sync_client,
    make_respan,
    print_result,
    root_request,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "agent-completions"


def response(request):
    payload = json.loads(request.content)
    assert payload["agent_id"] == "fixture-agent"
    if payload.get("stream"):
        return deterministic_stream_response(
            request,
            fragments=("Agent ", "response"),
            prompt_tokens=9,
            completion_tokens=3,
        )
    return deterministic_chat_response(
        request, content="Agent response", prompt_tokens=9, completion_tokens=3
    )


@workflow(name=workflow_name(EXAMPLE_NAME))
async def run(request: dict) -> dict:
    kwargs = {
        "agent_id": "fixture-agent",
        "messages": [{"role": "user", "content": request["prompt"]}],
    }
    with make_mock_sync_client(response) as client:
        sync_text = client.agents.complete(**kwargs).choices[0].message.content
        sync_stream = "".join(
            event.data.choices[0].delta.content or ""
            for event in client.agents.stream(**kwargs)
        )
    async with make_mock_async_client(response) as client:
        async_text = (
            (await client.agents.complete_async(**kwargs)).choices[0].message.content
        )
        events = await client.agents.stream_async(**kwargs)
        async_stream = "".join(
            [event.data.choices[0].delta.content or "" async for event in events]
        )
    result = {
        "sync": sync_text,
        "async": async_text,
        "sync_stream": sync_stream,
        "async_stream": async_stream,
    }
    assert set(result.values()) == {"Agent response"}
    return result


def main() -> None:
    respan = make_respan(EXAMPLE_NAME)
    identifier = make_custom_identifier(EXAMPLE_NAME)
    try:
        with example_attributes(EXAMPLE_NAME, identifier):
            result = asyncio.run(
                run(root_request(EXAMPLE_NAME, "Reply as the configured agent"))
            )
        print_result(EXAMPLE_NAME, identifier, result, "deterministic-current-sdk")
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
