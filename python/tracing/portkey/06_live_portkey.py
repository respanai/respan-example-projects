from __future__ import annotations

from _shared import (
    example_attributes,
    execution_id,
    finish_respan,
    live_configured,
    make_client,
    make_respan,
    marker,
    model_name,
    print_result,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "live-portkey"


@workflow(name=workflow_name(EXAMPLE_NAME))
def trace_live(prompt: str) -> dict[str, str]:
    client = make_client(live=True)
    try:
        response = client.chat.completions.create(
            model=model_name(live=True), messages=[{"role": "user", "content": prompt}]
        )
        return {"response": response.choices[0].message.content or ""}
    finally:
        client.close()


def main() -> None:
    if not live_configured():
        print("SKIP: live calls require RESPAN_PORTKEY_LIVE=1 and PORTKEY_API_KEY")
        return
    run_marker = marker()
    execution = execution_id()
    respan = make_respan(EXAMPLE_NAME, run_marker)
    try:
        with example_attributes(EXAMPLE_NAME, run_marker, execution, mode="live"):
            result = trace_live("Reply with exactly: live Portkey tracing works.")
        print_result(EXAMPLE_NAME, run_marker, result)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
