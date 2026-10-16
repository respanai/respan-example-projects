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
from respan import propagate_attributes, workflow

WORKFLOW_NAME = "litellm_respan_attributes.workflow"


@workflow(name=WORKFLOW_NAME)
def litellm_respan_attributes() -> str:
    with propagate_attributes(
        customer_identifier="litellm-example-user",
        thread_identifier="litellm-example-thread",
        metadata={"scenario": "attribute-propagation"},
    ):
        response = litellm.completion(
            **provider_client(),
            api_key=GATEWAY_API_KEY,
            api_base=GATEWAY_BASE_URL,
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": "Return a short JSON object with one key named status.",
                }
            ],
            temperature=0,
            max_tokens=80,
        )
    return response.choices[0].message.content


def main() -> None:
    respan = create_respan("litellm-respan-attributes")
    try:
        output = run_with_example_attributes(
            respan,
            workflow_name=WORKFLOW_NAME,
            action=litellm_respan_attributes,
        )
        print(output)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
