from __future__ import annotations

import time

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

EXAMPLE = "google-and-nested-failure"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_google_and_nested_failure")
def run(prompt: str) -> dict:
    google_request = {
        "model": "gemini-request-model",
        "systemInstruction": {"parts": [{"text": "Use tools safely."}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "tools": [{"functionDeclarations": [{"name": "weather", "parameters": {}}]}],
    }

    def operation(_recorder):
        logger.send_log(
            provider="google",
            request=google_request,
            response={
                "modelVersion": "gemini-response-model",
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [
                                {"text": "Checking."},
                                {
                                    "functionCall": {
                                        "name": "weather",
                                        "args": {"city": "Tokyo"},
                                    }
                                },
                            ],
                        }
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 7,
                    "candidatesTokenCount": 2,
                    "totalTokenCount": 9,
                    "cachedContentTokenCount": 3,
                },
            },
            options={"start_time": time.time(), "end_time": time.time()},
        )
        raise RuntimeError("outer failure after nested Google success")

    try:
        logger.log_request(
            request={"model": "outer-wrapper", "messages": []},
            operation=operation,
            provider="openai",
            additional_headers={"Helicone-Property-Nested": "failure"},
        )
    except RuntimeError as exc:
        if str(exc) != "outer failure after nested Google success":
            raise
        return {"nested_success": True, "outer_failure": True}
    raise AssertionError("expected nested failure path")


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        result = run("Call the weather function for Tokyo.")
    # Helicone Helpers sends the explicit nested Google log. It does not send
    # its helper-owned terminal log after the callback raises.
    assert_local_logs(1)
    print_result(EXAMPLE, RUN_MARKER, {"result": result, "local_logs": 1})
finally:
    finish_respan(respan)
