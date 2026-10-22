import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import litellm
from _shared import (
    GATEWAY_BASE_URL,
    create_respan,
    provider_client,
    run_with_example_attributes,
)
from respan import workflow

WORKFLOW_NAME = "litellm_expected_error.workflow"


@workflow(name=WORKFLOW_NAME)
def litellm_expected_error() -> str:
    try:
        litellm.completion(
            **provider_client(error=True),
            api_key="respan-example-intentionally-invalid",
            api_base=GATEWAY_BASE_URL,
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "This request should fail."}],
            max_tokens=20,
        )
    except (litellm.APIError, litellm.BadRequestError) as exc:
        return f"caught expected {type(exc).__name__}"
    raise RuntimeError(
        "The controlled invalid-credential request unexpectedly succeeded."
    )


def main() -> None:
    respan = create_respan("litellm-expected-error")
    try:
        output = run_with_example_attributes(
            respan,
            workflow_name=WORKFLOW_NAME,
            action=litellm_expected_error,
        )
        print(output)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
