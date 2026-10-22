from __future__ import annotations

from _shared import (
    example_attributes,
    finish_respan,
    make_client,
    make_custom_identifier,
    make_respan,
    model_name,
    print_result,
    print_start,
    workflow_name,
)
from respan import workflow
from together import APIStatusError

EXAMPLE_NAME = "expected-error"


@workflow(name=workflow_name(EXAMPLE_NAME))
def _expected_error_workflow(prompt: str) -> str:
    with make_client(error_status=429) as client:
        client.chat.completions.create(
            model=model_name(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=16,
        )
    return "unexpected success"


def run_expected_error() -> None:
    marker = make_custom_identifier(EXAMPLE_NAME)
    respan = make_respan(EXAMPLE_NAME, marker)
    result: dict[str, object] = {}
    try:
        with example_attributes(EXAMPLE_NAME, marker):
            print_start(EXAMPLE_NAME, marker)
            try:
                _expected_error_workflow("Trigger deterministic provider throttling.")
            except APIStatusError as exc:
                result = {
                    "expected_error": type(exc).__name__,
                    "status_code": getattr(exc, "status_code", None),
                }
            else:
                raise AssertionError("expected provider failure was not raised")
    finally:
        finish_respan(respan)
    print_result(EXAMPLE_NAME, marker, result)


if __name__ == "__main__":
    run_expected_error()
