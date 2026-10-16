import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import litellm
from _shared import (
    GATEWAY_API_KEY,
    GATEWAY_BASE_URL,
    MODEL,
    create_respan,
    provider_client,
    run_with_example_attributes,
)
from respan import workflow

WORKFLOW_NAME = "litellm_basic_completion.workflow"


@workflow(name=WORKFLOW_NAME)
def litellm_basic_completion() -> str:
    response = litellm.completion(
        **provider_client(),
        api_key=GATEWAY_API_KEY,
        api_base=GATEWAY_BASE_URL,
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": "In one sentence, explain what LiteLLM helps developers do.",
            }
        ],
        temperature=0.1,
        max_tokens=80,
    )
    return response.choices[0].message.content


def main() -> None:
    respan = create_respan("litellm-basic-completion")
    try:
        output = run_with_example_attributes(
            respan,
            workflow_name=WORKFLOW_NAME,
            action=litellm_basic_completion,
        )
        print(output)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
