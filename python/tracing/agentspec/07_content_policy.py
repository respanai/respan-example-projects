"""Respan content policy snapshots and standard OTel suppression."""

import os

from _fixtures import build_agent, fixture_model
from _shared import build_respan, example_scope
from opentelemetry import context
from opentelemetry.context import _SUPPRESS_INSTRUMENTATION_KEY
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def call(prompt):
    with fixture_model():
        return build_agent().invoke({"messages": [{"role": "user", "content": prompt}]})


def main():
    respan = build_respan("content-policy")
    with example_scope("content-policy"):
        try:
            previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
            os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
            try:
                assert call("private-env-prompt")
            finally:
                if previous is None:
                    os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
                else:
                    os.environ["TRACELOOP_TRACE_CONTENT"] = previous
            token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
            try:
                assert call("private-context-prompt")
            finally:
                context.detach(token)
            token = context.attach(
                context.set_value(_SUPPRESS_INSTRUMENTATION_KEY, True)
            )
            try:
                assert call("suppressed-prompt")
            finally:
                context.detach(token)
            print({"private_calls": 2, "suppressed_calls": 1})
        finally:
            respan.shutdown()


if __name__ == "__main__":
    main()
