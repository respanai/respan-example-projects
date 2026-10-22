"""Per-call content policy and standard OpenTelemetry suppression."""

import os

from _shared import (
    create_respan,
    deterministic_chat_client,
    deterministic_watson_runtime,
    example_attributes,
    marker_for,
    workflow_name,
)
from opentelemetry import context
from opentelemetry.context import _SUPPRESS_INSTRUMENTATION_KEY
from respan import workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

EXAMPLE_NAME = "content-policy"


@workflow(name=workflow_name(EXAMPLE_NAME))
def content_policy(scenario: str) -> dict:
    client = deterministic_chat_client()
    prior = os.environ.get("TRACELOOP_TRACE_CONTENT")
    os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
    try:
        client.generate_response("private-environment-prompt")
    finally:
        if prior is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = prior
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        client.generate_response("private-context-prompt")
    finally:
        context.detach(token)
    token = context.attach(context.set_value(_SUPPRESS_INSTRUMENTATION_KEY, True))
    try:
        client.generate_response("suppressed-private-prompt")
    finally:
        context.detach(token)
    return {"scenario": scenario, "expected_child_spans": 2, "content_captured": False}


def main():
    marker = marker_for(EXAMPLE_NAME)
    with deterministic_watson_runtime():
        respan = create_respan(EXAMPLE_NAME, marker)
        try:
            with example_attributes(EXAMPLE_NAME, marker):
                result = content_policy("environment-context-suppression")
        finally:
            respan.shutdown()
    print({"example": EXAMPLE_NAME, "marker": marker, "result": result}, flush=True)


if __name__ == "__main__":
    main()
