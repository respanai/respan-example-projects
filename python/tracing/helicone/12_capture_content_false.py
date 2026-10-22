from __future__ import annotations

from _shared import (
    assert_local_logs,
    example_attributes,
    execution_id,
    finish_respan,
    make_logger,
    make_respan,
    marker,
    print_result,
)
from respan import workflow

EXAMPLE = "capture-content-false"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER, capture_content=False)
logger = make_logger()


@workflow(name="helicone_capture_content_false")
def run(prompt: str) -> str:
    def operation(recorder):
        response = {
            "model": "private-response-model",
            "choices": [
                {"message": {"role": "assistant", "content": "private output"}}
            ],
            "usage": {
                "prompt_tokens": 3,
                "completion_tokens": 2,
                "total_tokens": 5,
            },
        }
        recorder.append_results(response)
        return "content-suppressed"

    return logger.log_request(
        request={
            "model": "private-request-model",
            "messages": [{"role": "user", "content": prompt}],
        },
        operation=operation,
        provider="openai",
    )


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        outcome = run("This prompt must not be exported by the child span.")
    assert_local_logs(1, path_suffix="/oai/v1/log")
    print_result(EXAMPLE, RUN_MARKER, {"outcome": outcome, "local_logs": 1})
finally:
    finish_respan(respan)
