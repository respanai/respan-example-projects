"""Preserve a model exception and close a partially consumed stream."""

from _shared import FixtureModel, build_respan, example_attributes, response
from opentelemetry import trace
from respan import workflow

EXAMPLE_NAME = "model-failure-and-stream-close"
WORKFLOW_NAME = "smolagents_failure_stream_close_workflow"


@workflow(name=WORKFLOW_NAME)
def execute_failure_and_close(label: str) -> str:
    error = ValueError("controlled smolagents model failure")
    try:
        FixtureModel([error]).generate([{"role": "user", "content": label}])
    except ValueError as raised:
        assert raised is error
    else:
        raise AssertionError("Model exception did not propagate")
    current = trace.get_current_span()
    stream = FixtureModel([response("partially consumed fixture")]).generate_stream(
        [{"role": "user", "content": label}]
    )
    assert trace.get_current_span() is current
    next(stream)
    assert trace.get_current_span() is current
    stream.close()
    assert trace.get_current_span() is current
    return "model error and stream close preserved"


def main():
    respan = build_respan(EXAMPLE_NAME, WORKFLOW_NAME)
    try:
        with example_attributes(EXAMPLE_NAME, WORKFLOW_NAME):
            print(
                execute_failure_and_close(
                    "Verify controlled failure and stream closure"
                )
            )
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
