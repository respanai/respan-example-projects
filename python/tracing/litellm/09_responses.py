import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

"""Native LiteLLM Responses current calls and sync/async streaming."""
import asyncio

import litellm
from _fixtures import response_client
from _shared import MODE, create_respan, run_with_example_attributes
from respan import workflow

WORKFLOW_NAME = "litellm_responses.workflow"


@workflow(name=WORKFLOW_NAME)
def run():
    arguments = {
        "model": "openai/gpt-4o-mini",
        "input": [
            {
                "type": "function_call",
                "call_id": "historical-response-call-id",
                "name": "lookup",
                "arguments": '{"value":1}',
            },
            {
                "type": "function_call_output",
                "call_id": "historical-response-call-id",
                "output": "historical result",
            },
            {"role": "user", "content": "controlled source"},
        ],
        "api_key": "fixture-only",
        "api_base": "https://fixture.invalid/v1",
    }
    response = litellm.responses(**arguments, client=response_client(tools=True))
    assert response.output[0].call_id == "current-response-call-id"
    stream = litellm.responses(
        **arguments, stream=True, client=response_client(tools=True, stream=True)
    )
    assert len(list(stream)) > 0

    async def asynchronous():
        response = await litellm.aresponses(
            **arguments, client=response_client(async_=True)
        )
        assert response.output[0].content[0].text == "controlled response"
        stream = await litellm.aresponses(
            **arguments, stream=True, client=response_client(async_=True, stream=True)
        )
        count = 0
        async for _ in stream:
            count += 1
        assert count > 0

    asyncio.run(asynchronous())
    return {"responses_sync_async_streams": "verified"}


def main():
    if MODE != "fixture":
        print("SKIP: Responses fixtures use controlled provider bodies")
        return
    respan = create_respan("litellm-responses")
    try:
        print(
            run_with_example_attributes(respan, workflow_name=WORKFLOW_NAME, action=run)
        )
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
