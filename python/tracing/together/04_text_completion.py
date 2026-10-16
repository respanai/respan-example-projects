from __future__ import annotations

from _shared import (
    completion_model_name,
    example_attributes,
    finish_respan,
    first_text_completion,
    make_client,
    make_custom_identifier,
    make_respan,
    print_result,
    print_start,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "text-completion"


@workflow(name=workflow_name(EXAMPLE_NAME))
def _text_completion_workflow(prompt: str) -> str:
    with make_client() as client:
        response = client.completions.create(
            model=completion_model_name(),
            prompt=prompt,
            max_tokens=40,
            temperature=0,
        )
        return first_text_completion(response)


def run_text_completion() -> None:
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    respan = make_respan(EXAMPLE_NAME, custom_identifier)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print_start(EXAMPLE_NAME, custom_identifier)
            text = _text_completion_workflow(
                "Complete this sentence in under ten words: Tracing AI calls helps"
            )
    finally:
        finish_respan(respan)

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    run_text_completion()
