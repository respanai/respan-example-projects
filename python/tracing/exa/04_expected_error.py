from __future__ import annotations

from _shared import clients, example_attributes, finish, make_respan
from respan import workflow

EXAMPLE = "expected-error"


@workflow(name="exa_python_expected_error")
def expected_error(client) -> str:
    try:
        client.search("expected Exa provider error", num_results=1)
    except Exception as exc:  # noqa: BLE001 - this scenario validates error spans.
        return f"{type(exc).__name__}: {exc}"
    raise AssertionError("expected the deterministic Exa request to fail")


def main() -> None:
    respan = make_respan(EXAMPLE)
    try:
        with clients() as (client, _async_client, mode):
            if mode == "live":
                print("Skipping destructive expected-error request in live mode.")
                return
            with example_attributes(EXAMPLE, mode) as workflow_name:
                result = expected_error(client)
                print({"workflow_name": workflow_name, "mode": mode, "error": result})
    finally:
        finish(respan)


if __name__ == "__main__":
    main()
