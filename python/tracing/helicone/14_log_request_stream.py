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

EXAMPLE = "log-request-stream"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_log_request_stream")
def run(prompt: str) -> str:
    def operation(recorder):
        chunks = [
            {
                "model": "documented-stream-response",
                "choices": [{"delta": {"content": "Documented "}}],
            },
            {
                "model": "documented-stream-response",
                "choices": [{"delta": {"content": "chunks work."}}],
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 3,
                    "total_tokens": 8,
                },
            },
        ]
        recorder.append_results({"chunks": chunks, "time_to_first_token_ms": 14.25})
        return "Documented chunks work."

    return logger.log_request(
        request={
            "model": "documented-stream-request",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        },
        operation=operation,
        provider="openai",
        additional_headers={"Helicone-Property-Stream": "log-request"},
    )


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        output = run("Exercise the documented chunks response shape.")
    assert_local_logs(1, path_suffix="/oai/v1/log")
    print_result(EXAMPLE, RUN_MARKER, {"output": output, "local_logs": 1})
finally:
    finish_respan(respan)
