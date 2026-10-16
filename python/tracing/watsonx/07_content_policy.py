from _shared import GEN, close, native, run_case
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def action(provider):
    c, m, _e, _requests, _responses, _body, *_ = native(frames=[GEN, GEN])
    try:
        s = m.generate_text_stream(
            prompt="private-controlled-late-veto", raw_response=True
        )
        assert next(s) == GEN
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        try:
            assert next(s) == GEN
        finally:
            context.detach(token)
        s.close()
    finally:
        close(c)
    c, m, *_ = native(GEN)
    try:
        with provider.get_tracer("watsonx.examples").start_as_current_span(
            "private_application_parent", attributes={ENABLE_CONTENT_TRACING_KEY: False}
        ) as parent:
            parent.set_attribute(ENABLE_CONTENT_TRACING_KEY, True)
            assert (
                m.generate(prompt="private-controlled-ancestor")["results"]
                == GEN["results"]
            )
    finally:
        close(c)
    return "irreversible late stream and initial ancestor veto"


if __name__ == "__main__":
    run_case("watsonx_content_policy", action)
