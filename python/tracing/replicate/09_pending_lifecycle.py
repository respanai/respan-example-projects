import gc

from _native import Native
from _shared import Runtime

r = Runtime("pending_lifecycle")
n = Native(chunks=2)
try:
    with r.workflow():
        first = n.client.stream(
            "owner/model", input={"prompt": "First pending request"}
        )
        second = n.client.stream(
            "owner/model", input={"prompt": "Second pending request"}
        )
        assert len(list(first)) == 3
        assert len(list(second)) == 3
        abandoned = n.client.stream(
            "owner/model", input={"prompt": "Unconsumed request"}
        )
        del abandoned
        gc.collect()
    spans = r.memory.get_finished_spans()
    assert "traceloop.entity.output" in spans[0].attributes
    assert "traceloop.entity.output" in spans[1].attributes
    assert "traceloop.entity.output" not in spans[2].attributes
finally:
    n.close()
    r.close()
