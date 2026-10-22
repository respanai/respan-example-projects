import pytest
from opentelemetry import trace
from opentelemetry.semconv_ai import SpanAttributes
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE


def test_nested_application_task():
    with trace.get_tracer("application").start_as_current_span(
        "calculate_total"
    ) as span:
        span.set_attribute(RESPAN_LOG_TYPE, "task")
        span.set_attribute(
            SpanAttributes.TRACELOOP_ENTITY_INPUT, '{"subtotal":40,"tax":2}'
        )
        total = 40 + 2
        span.set_attribute(SpanAttributes.TRACELOOP_ENTITY_OUTPUT, "42")
        assert total == 42


@pytest.mark.parametrize(
    "value",
    [
        {
            "vector": list(range(5000)),
            "zero": 0,
            "false": False,
            "api_key": "controlled secret",
        }
    ],
    ids=["native-json"],
)
def test_complete_native_json(value):
    assert value["vector"][-1] == 4999 and value["false"] is False


@pytest.mark.skip(reason="controlled skip")
def test_skip():
    pass


@pytest.mark.xfail(reason="controlled expected failure")
def test_xfail():
    assert False


@pytest.mark.xfail(reason="controlled XPASS")
def test_xpass():
    pass
