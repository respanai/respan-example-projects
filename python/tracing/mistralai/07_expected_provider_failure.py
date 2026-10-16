from __future__ import annotations

from _shared import (
    example_attributes,
    finish_respan,
    httpx,
    make_custom_identifier,
    make_mock_sync_client,
    make_respan,
    print_result,
    print_start,
    root_request,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "expected-provider-failure"
PROMPT = "Exercise a deterministic provider authentication failure."


def _response(request):
    return httpx.Response(
        401,
        json={"message": "invalid api key", "request_id": "fixture_request"},
        request=request,
    )


def _build_provider_failure_workflow(client):
    @workflow(name=workflow_name(EXAMPLE_NAME))
    def run(request: dict[str, str]) -> None:
        client.chat.complete(
            model=request["model"],
            messages=[{"role": "user", "content": request["prompt"]}],
        )
        raise AssertionError("provider failure fixture unexpectedly succeeded")

    return run


def run_expected_provider_failure() -> None:
    respan = make_respan(EXAMPLE_NAME)
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    result: dict[str, object] = {}

    try:
        with (
            make_mock_sync_client(_response) as client,
            example_attributes(EXAMPLE_NAME, custom_identifier),
        ):
            print_start(EXAMPLE_NAME, custom_identifier, "deterministic-current-sdk")
            try:
                _build_provider_failure_workflow(client)(
                    root_request(EXAMPLE_NAME, PROMPT, expected_status=401)
                )
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)
                if status_code != 401:
                    raise
                result = {
                    "expected": True,
                    "error_type": type(exc).__name__,
                    "status_code": status_code,
                }
    finally:
        finish_respan(respan)

    print_result(
        EXAMPLE_NAME,
        custom_identifier,
        result,
        "deterministic-current-sdk",
    )


if __name__ == "__main__":
    run_expected_provider_failure()
