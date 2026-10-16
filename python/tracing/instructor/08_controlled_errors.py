"""Controlled provider and validation failures, plus current retry token budget."""

import inspect

from _fixtures import client_context
from _respan_instructor import (
    User,
    attributes,
    create_respan_instructor_client,
    retry_exception_type,
    workflow,
)


@workflow(name="instructor_example_08_controlled_errors")
def failures(client):
    RetryError = retry_exception_type()
    names = []
    try:
        client.create(
            response_model=User,
            messages=[{"role": "user", "content": "Controlled provider failure."}],
            max_retries=0,
        )
    except RetryError as error:
        names.append(type(error).__name__)
    with client_context(invalid_attempts=20) as (invalid, _):
        kwargs = (
            {"token_budget": 1}
            if "token_budget" in inspect.signature(invalid.create).parameters
            else {}
        )
        try:
            invalid.create(
                response_model=User,
                messages=[
                    {"role": "user", "content": "Controlled validation failure."}
                ],
                model="fixture-model",
                max_retries=1,
                **kwargs,
            )
        except (RetryError, ValueError) as error:
            names.append(type(error).__name__)
    assert len(names) == 2
    return {"controlled_errors": names, "budget_available": bool(kwargs)}


def main():
    tracing, client = create_respan_instructor_client(
        app_name="instructor-errors", status=401
    )
    try:
        with attributes("08_controlled_errors.py"):
            print(failures(client))
    finally:
        tracing.shutdown()


if __name__ == "__main__":
    main()
