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

EXAMPLE = "log-request-error"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_log_request_error")
def run(trigger_prompt: str) -> str:
    def operation(_recorder):
        raise ValueError("deterministic log_request failure")

    try:
        logger.log_request(
            request={
                "model": "local-error-model",
                "messages": [{"role": "user", "content": trigger_prompt}],
            },
            operation=operation,
            provider="openai",
        )
    except ValueError as exc:
        if str(exc) != "deterministic log_request failure":
            raise
        return "expected-error-captured"
    raise AssertionError("expected log_request to raise")


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        outcome = run("Trigger the synchronous error fallback.")
    # Helicone 1.2.1 does not call its sink when the operation raises; the
    # Respan instrumentation emits an error span from the outer method instead.
    assert_local_logs(0)
    print_result(EXAMPLE, RUN_MARKER, {"outcome": outcome, "local_logs": 0})
finally:
    finish_respan(respan)
