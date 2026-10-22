import json

from _native import Native
from _shared import Runtime

r = Runtime("streaming")
n = Native(chunks=250)
try:
    with r.workflow():
        stream = n.client.stream(
            "owner/model", input={"prompt": "Stream controlled output"}
        )
        assert not n.calls
        events = list(stream)
        assert len(events) == 251 and events[-2].data == "chunk-249"
        partial = n.client.stream(
            "owner/model", input={"prompt": "Close after one event"}
        )
        assert next(partial).data == "chunk-0"
        partial.close()
        empty = n.client.stream(
            "owner/model", input={"prompt": "Close without reading"}
        )
        empty.close()
    spans = r.memory.get_finished_spans()
    assert len(json.loads(spans[0].attributes["traceloop.entity.output"])) == 251
    assert spans[0].attributes["gen_ai.completion.0.content"] == "".join(
        event.data for event in events[:-1]
    )
    assert "traceloop.entity.output" not in spans[2].attributes
    assert all(response.is_closed for response in n.responses)
finally:
    n.close()
    r.close()
