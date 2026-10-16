import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import asyncio

import litellm
from _shared import (
    GATEWAY_API_KEY,
    GATEWAY_BASE_URL,
    MODEL,
    create_respan,
    provider_client,
    run_async_with_example_attributes,
)
from respan import workflow

WORKFLOW_NAME = "litellm_async_completion.workflow"


@workflow(name=WORKFLOW_NAME)
async def litellm_async_completion() -> str:
    response = await litellm.acompletion(
        **provider_client(asynchronous=True),
        api_key=GATEWAY_API_KEY,
        api_base=GATEWAY_BASE_URL,
        model=MODEL,
        messages=[{"role": "user", "content": "Reply with: async LiteLLM works."}],
        temperature=0,
        max_tokens=30,
    )
    return response.choices[0].message.content


def main() -> None:
    respan = create_respan("litellm-async-completion")
    try:
        print(
            asyncio.run(
                run_async_with_example_attributes(
                    respan,
                    workflow_name=WORKFLOW_NAME,
                    action=litellm_async_completion,
                )
            )
        )
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
