from __future__ import annotations

import asyncio
import json

from _shared import (
    deterministic_chat_response,
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
from pydantic import BaseModel
from respan import workflow

EXAMPLE_NAME = "structured-output"


class Answer(BaseModel):
    answer: int


def response(request):
    payload = json.loads(request.content)
    assert payload["response_format"]["type"] == "json_schema"
    return deterministic_chat_response(
        request, content='{"answer":42}', prompt_tokens=7, completion_tokens=4
    )


@workflow(name=workflow_name(EXAMPLE_NAME))
async def run(request: dict) -> dict:
    kwargs = {
        "model": request["model"],
        "messages": [{"role": "user", "content": request["prompt"]}],
        "response_format": Answer,
    }
    with make_mock_sync_client(response) as client:
        sync_result = client.chat.parse(**kwargs).choices[0].message.parsed
    async with make_mock_async_client(response) as client:
        async_result = (
            (await client.chat.parse_async(**kwargs)).choices[0].message.parsed
        )
    assert sync_result.answer == async_result.answer == 42
    return {"sync": sync_result.model_dump(), "async": async_result.model_dump()}


def main() -> None:
    respan = make_respan(EXAMPLE_NAME)
    identifier = make_custom_identifier(EXAMPLE_NAME)
    try:
        with example_attributes(EXAMPLE_NAME, identifier):
            result = asyncio.run(
                run(root_request(EXAMPLE_NAME, "Return the answer as JSON"))
            )
        print_result(EXAMPLE_NAME, identifier, result, "deterministic-current-sdk")
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
