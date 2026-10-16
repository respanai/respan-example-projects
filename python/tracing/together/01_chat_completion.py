from __future__ import annotations

from _shared import (
    example_attributes,
    finish_respan,
    first_message_text,
    make_client,
    make_custom_identifier,
    make_respan,
    model_name,
    print_result,
    print_start,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "chat-completion"


@workflow(name=workflow_name(EXAMPLE_NAME))
def _chat_completion_workflow(prompt: str) -> str:
    with make_client() as client:
        response = client.chat.completions.create(
            model=model_name(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0,
        )
        return first_message_text(response)


def run_chat_completion() -> None:
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    respan = make_respan(EXAMPLE_NAME, custom_identifier)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print_start(EXAMPLE_NAME, custom_identifier)
            text = _chat_completion_workflow(
                "Reply with one concise sentence about tracing Together AI apps."
            )
    finally:
        finish_respan(respan)

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    run_chat_completion()
