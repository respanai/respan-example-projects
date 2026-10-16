"""Actual partial/error/early-close streams and a delayed private parent veto."""

from __future__ import annotations

import json

from _controlled import Provider, model
from _shared import create_respan, finish_respan, workflow_attributes
from mirascope import llm
from opentelemetry import context, trace
from respan import workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


@workflow(name="mirascope-native-stream-errors")
def errors():
    failures = 0
    for chunks in (
        [
            llm.ServerError(
                "controlled before-yield failure",
                provider="controlled",
                status_code=503,
            )
        ],
        [
            llm.TextStartChunk(),
            llm.TextChunk(delta="actual partial result"),
            llm.ServerError(
                "controlled partial failure", provider="controlled", status_code=503
            ),
        ],
    ):
        native, _ = model(Provider(chunks=chunks))
        try:
            list(native.stream("stream error fixture").text_stream())
        except llm.ServerError as error:
            assert error is chunks[-1]
            failures += 1
    native, _ = model()
    native.stream("early-close fixture")._chunk_iterator.close()
    return {"expected_failures": failures, "unadvanced_closes": 1}


@workflow(name="mirascope-native-delayed-veto")
def privacy():
    native, _ = model()
    with trace.get_tracer("example").start_as_current_span("parent-veto"):
        response = native.stream("PRIVATE delayed payload")
        context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    assert "native stream" in "".join(response.text_stream())
    return {"private_response_consumed": True}


def main():
    runtime = create_respan("mirascope-stream-errors-veto")
    try:
        with runtime.propagate_attributes(
            **workflow_attributes("mirascope-native-stream-errors", __file__)
        ):
            print(json.dumps(errors()))
        with runtime.propagate_attributes(
            **workflow_attributes("mirascope-native-delayed-veto", __file__)
        ):
            print(json.dumps(privacy()))
    finally:
        finish_respan(runtime)


if __name__ == "__main__":
    main()
