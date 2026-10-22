"""Environment start bound and Respan context veto, including raw metadata."""

import os

import agentops
from _shared import build_respan
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def main():
    telemetry = build_respan(example_name="privacy", workflow_name="agentops_privacy")
    prior = os.environ.get("TRACELOOP_TRACE_CONTENT")
    tokens = []

    @agentops.task(name="private_start")
    def private_start(value):
        os.environ["TRACELOOP_TRACE_CONTENT"] = "true"
        agentops.update_trace_metadata({"note": "PRIVATE_DYNAMIC"})
        return value

    @agentops.task(name="private_end")
    def private_end(value):
        tokens.append(
            context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        )
        return value

    try:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        assert private_start("PRIVATE_START") == "PRIVATE_START"
        assert private_end("PRIVATE_END") == "PRIVATE_END"
    finally:
        for token in reversed(tokens):
            context.detach(token)
        if prior is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = prior
        telemetry.shutdown()


if __name__ == "__main__":
    main()
