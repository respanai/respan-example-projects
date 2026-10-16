"""Native partial results, including early close where the SDK returns an iterator."""

from _respan_instructor import (
    User,
    attributes,
    create_respan_instructor_client,
    workflow,
)
from opentelemetry import trace


@workflow(name="instructor_example_07_partial_stream")
def partial(client):
    original = trace.get_current_span()
    response = client.create_partial(
        response_model=User,
        messages=[{"role": "user", "content": "Extract Ada, age36."}],
    )
    assert trace.get_current_span() is original
    iterator = iter(response)
    first = next(iterator)
    close = getattr(iterator, "close", None)
    if close is not None:
        close()
    assert trace.get_current_span() is original
    return {
        "native_type": type(response).__name__,
        "first": first.model_dump(),
        "supports_close": close is not None,
    }


def main():
    tracing, client = create_respan_instructor_client(app_name="instructor-partial")
    try:
        with attributes("07_partial_stream.py"):
            print(partial(client))
    finally:
        tracing.shutdown()


if __name__ == "__main__":
    main()
