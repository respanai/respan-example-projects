from __future__ import annotations

import json

from _shared import (
    example_attributes,
    example_run_id,
    finish_respan,
    make_respan,
    print_result,
    tracer,
    workflow,
    workflow_name,
)
from opentelemetry.trace import Status, StatusCode

EXAMPLE_NAME = "expected-failure"
ERROR_MESSAGE = "openinference deterministic provider failure"


@workflow(name=workflow_name(EXAMPLE_NAME))
def expected_failure_workflow(operation: str) -> None:
    error = RuntimeError(ERROR_MESSAGE)
    with tracer().start_as_current_span("openai.chat.failure") as span:
        span.set_attribute("openinference.span.kind", "LLM")
        span.set_attribute("llm.model_name", "gpt-4.1-mini")
        span.set_attribute("llm.system", "openai")
        span.set_attribute("llm.provider", "openai")
        span.set_attribute("input.value", json.dumps({"operation": operation}))
        span.record_exception(error)
        span.set_status(Status(StatusCode.ERROR, ERROR_MESSAGE))
    raise error


def run() -> None:
    run_id = example_run_id()
    respan = make_respan(EXAMPLE_NAME, run_id)
    observed = ""
    try:
        with example_attributes(EXAMPLE_NAME, run_id):
            expected_failure_workflow("validate provider error translation")
    except RuntimeError as error:
        if str(error) != ERROR_MESSAGE:
            raise
        observed = f"observed expected error: {error}"
    finally:
        finish_respan(respan)
    print_result(EXAMPLE_NAME, run_id, observed)


if __name__ == "__main__":
    run()
