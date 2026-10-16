from __future__ import annotations

from typing import Any

from _shared import (
    example_attributes,
    execution_id,
    finish_respan,
    make_client,
    make_respan,
    marker,
    print_result,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "expected-error"


@workflow(name=workflow_name(EXAMPLE_NAME))
def trace_expected_error(prompt: str) -> None:
    client = make_client()
    try:
        client.chat.completions.create(
            model="error-401", messages=[{"role": "user", "content": prompt}]
        )
    finally:
        client.close()


def _status_code(exc: BaseException) -> int | None:
    value: Any = getattr(exc, "status_code", None)
    return value if isinstance(value, int) else None


def main() -> None:
    run_marker = marker()
    execution = execution_id()
    respan = make_respan(EXAMPLE_NAME, run_marker)
    try:
        try:
            with example_attributes(
                EXAMPLE_NAME,
                run_marker,
                execution,
                mode="deterministic-error",
            ):
                trace_expected_error("Exercise the Portkey provider failure path.")
        except Exception as exc:  # noqa: BLE001 - this is the expected SDK failure path
            print_result(
                EXAMPLE_NAME,
                run_marker,
                {
                    "expected_error": type(exc).__name__,
                    "status_code": _status_code(exc),
                },
            )
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
