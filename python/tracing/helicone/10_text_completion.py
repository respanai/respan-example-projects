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

EXAMPLE = "text-completion"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_text_completion")
def run(prompt: str) -> str:
    request = {"model": "local-helicone-text", "prompt": prompt}

    def operation(recorder):
        response = {
            "model": "local-helicone-text",
            "choices": [{"text": " observable and testable."}],
            "usage": {
                "prompt_tokens": 4,
                "completion_tokens": 4,
                "total_tokens": 8,
            },
        }
        recorder.append_results(response)
        return response["choices"][0]["text"]

    return logger.log_request(
        request=request,
        operation=operation,
        provider="custom-text-provider",
    )


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        output = run("Manual logging is")
    assert_local_logs(1)
    print_result(EXAMPLE, RUN_MARKER, {"output": output, "local_logs": 1})
finally:
    finish_respan(respan)
