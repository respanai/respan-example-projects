from __future__ import annotations

from _shared import (
    example_attributes,
    make_client,
    make_custom_identifier,
    make_respan,
    model_name,
    print_result,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "generate-content"


@workflow(name=workflow_name(EXAMPLE_NAME))
def _generate_content_workflow(prompt: str) -> str:
    client = make_client()
    response = client.models.generate_content(
        model=model_name(),
        contents=prompt,
    )
    return response.text or ""


def run_generate_content() -> None:
    respan = make_respan(EXAMPLE_NAME)
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print(f"custom_identifier={custom_identifier}", flush=True)
            print(f"workflow_name={workflow_name(EXAMPLE_NAME)}", flush=True)
            text = _generate_content_workflow(
                "Reply with one concise sentence about observability for Gemini apps."
            )
    finally:
        respan.shutdown()

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    run_generate_content()
