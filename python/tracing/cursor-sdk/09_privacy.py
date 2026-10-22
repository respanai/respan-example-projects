import os

from _fixtures import Fixture, events
from _shared import make_custom_identifier, make_event, tracing
from opentelemetry import context, trace
from opentelemetry.semconv_ai import SpanAttributes
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def main():
    marker = make_custom_identifier("privacy")
    with tracing("privacy", run_id=marker) as (inst, memory):
        previous = os.environ.get("TRACELOOP_TRACE_CONTENT")
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
        try:
            inst.process_event(
                make_event(
                    "privacy", marker, "beforeSubmitPrompt", prompt="PRIVATE prompt"
                )
            )
            with Fixture(rows=events(tools=True)).client() as client:
                run = Fixture.agent(client).send("PRIVATE native prompt")
                os.environ["TRACELOOP_TRACE_CONTENT"] = "true"
                run.wait()
            inst.process_event(
                make_event(
                    "privacy",
                    marker,
                    "postToolUseFailure",
                    tool_name="Shell",
                    tool_input={"command": "PRIVATE command"},
                    error_message="PRIVATE error",
                    failure_type="error",
                )
            )
            inst.process_event(make_event("privacy", marker, "stop", status="error"))
            rows = events(status="error")
            rows[-1]["result"]["result"]["error"]["message"] = (
                "PRIVATE controlled diagnostic"
            )
            with Fixture(rows=rows).client() as client:
                run = Fixture.agent(client).send("PRIVATE late-veto prompt")

                def on_status(status):
                    if status == "error":
                        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"

                run.on_did_change_status(on_status)
                assert run.wait().status == "error"
            inst.deactivate()
            os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
            with trace.get_tracer("fixture").start_as_current_span(
                "preexisting-parent",
                attributes={
                    RESPAN_LOG_TYPE: "task",
                    SpanAttributes.TRACELOOP_ENTITY_NAME: "preexisting-parent",
                    SpanAttributes.TRACELOOP_ENTITY_PATH: "",
                },
            ):
                inst.activate()
                os.environ["TRACELOOP_TRACE_CONTENT"] = "true"
                with Fixture().client() as client:
                    assert (
                        Fixture.agent(client)
                        .send("PRIVATE native prompt")
                        .wait()
                        .result
                        == "Fixture completion"
                    )
                inst.process_event(
                    make_event(
                        "unobserved-parent",
                        marker,
                        "beforeSubmitPrompt",
                        prompt="PRIVATE hook prompt",
                    )
                )
                inst.process_event(
                    make_event("unobserved-parent", marker, "stop", status="completed")
                )
            supplied = context.set_value(ENABLE_CONTENT_TRACING_KEY, True)
            private = context.attach(
                context.set_value(ENABLE_CONTENT_TRACING_KEY, False)
            )
            try:
                with trace.get_tracer("fixture").start_as_current_span(
                    "supplied-context-parent",
                    context=supplied,
                    attributes={
                        RESPAN_LOG_TYPE: "task",
                        SpanAttributes.TRACELOOP_ENTITY_NAME: "supplied-context-parent",
                        SpanAttributes.TRACELOOP_ENTITY_PATH: "",
                    },
                ):
                    enabled = context.attach(
                        context.set_value(ENABLE_CONTENT_TRACING_KEY, True)
                    )
                    try:
                        with Fixture().client() as client:
                            assert (
                                Fixture.agent(client)
                                .send("PRIVATE native prompt")
                                .wait()
                                .result
                                == "Fixture completion"
                            )
                        inst.process_event(
                            make_event(
                                "supplied-context-parent",
                                marker,
                                "beforeSubmitPrompt",
                                prompt="PRIVATE hook prompt",
                            )
                        )
                        inst.process_event(
                            make_event(
                                "supplied-context-parent",
                                marker,
                                "stop",
                                status="completed",
                            )
                        )
                    finally:
                        context.detach(enabled)
            finally:
                context.detach(private)
        finally:
            if previous is None:
                os.environ.pop("TRACELOOP_TRACE_CONTENT", None)
            else:
                os.environ["TRACELOOP_TRACE_CONTENT"] = previous
        assert all(
            "PRIVATE" not in str(s.attributes) for s in memory.get_finished_spans()
        )
        assert "PRIVATE" not in inst._processor.state_path.read_text()
        assert all(
            "PRIVATE" not in str(s.status.description)
            for s in memory.get_finished_spans()
        )


if __name__ == "__main__":
    main()
