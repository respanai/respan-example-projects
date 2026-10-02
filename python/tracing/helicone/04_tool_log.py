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

EXAMPLE = "tool-log"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_tool_log")
def run(city: str) -> dict:
    def operation(recorder):
        result = {"city": city, "temperature_f": 72, "condition": "sunny"}
        recorder.append_results(result)
        return result

    return logger.log_request(
        request={
            "_type": "tool",
            "toolName": "get_weather",
            "input": {"city": city},
        },
        operation=operation,
    )


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        result = run("Tokyo")
    assert_local_logs(1)
    print_result(EXAMPLE, RUN_MARKER, {"result": result, "local_logs": 1})
finally:
    finish_respan(respan)
