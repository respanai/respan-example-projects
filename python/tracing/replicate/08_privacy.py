from _native import Native
from _shared import Runtime
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

r = Runtime("privacy")
n = Native("PRIVATE controlled result")
try:
    with r.workflow():
        a = n.client.stream("owner/model", input={"prompt": "PRIVATE request"})
        assert next(a).data == "chunk-0"
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        context.detach(token)
        list(a)
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        try:
            assert (
                n.client.run("owner/model", input={"prompt": "PRIVATE request"})
                == n.output
            )
        finally:
            context.detach(token)
    spans = r.memory.get_finished_spans()
    for span in spans[:2]:
        assert "traceloop.entity.input" not in span.attributes
        assert "traceloop.entity.output" not in span.attributes
        assert not any(
            key.startswith("respan.metadata.replicate") for key in span.attributes
        )
finally:
    n.close()
    r.close()
