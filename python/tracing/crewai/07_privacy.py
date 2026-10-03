"""Per-event content snapshots, context opt-out, and OTel suppression."""

import asyncio
import os

from _fixtures import FixtureServer
from _shared import create_respan, run_with_attributes, shutdown_respan
from opentelemetry import context as otel_context
from opentelemetry.instrumentation.utils import suppress_instrumentation
from respan import workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


@workflow(name="crewai_07_privacy")
def run_privacy(scenario: str) -> dict:
    previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
    try:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        FixtureServer().llm().call("private-environment-fixture")
        server = FixtureServer()
        server.before_response = lambda: os.environ.__setitem__(
            "TRACELOOP_TRACE_CONTENT", "true"
        )
        asyncio.run(server.llm().acall("private-snapshot-fixture"))
        token = otel_context.attach(
            otel_context.set_value(ENABLE_CONTENT_TRACING_KEY, False)
        )
        try:
            FixtureServer().llm(stream=True).call("private-context-stream-fixture")
        finally:
            otel_context.detach(token)
        with suppress_instrumentation():
            FixtureServer().llm().call("suppressed-fixture")
    finally:
        if previous is None:
            os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
        else:
            os.environ["TRACELOOP_TRACE_CONTENT"] = previous
    return {"scenario": scenario, "private_calls": 3, "suppressed_calls": 1}


def main():
    context = create_respan(
        app_name="crewai-07-privacy",
        example_name="07_privacy",
        workflow_name="crewai_07_privacy",
    )
    try:
        print(run_with_attributes(context, lambda: run_privacy("content-policy")))
    finally:
        shutdown_respan(context)


if __name__ == "__main__":
    main()
