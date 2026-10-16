from _native import Native
from _shared import Runtime
from replicate.exceptions import ModelError, ReplicateError

r = Runtime("provider_errors")
try:
    with r.workflow():
        for native, expected in [
            (Native(http_status=429), ReplicateError),
            (Native(status="failed"), ModelError),
        ]:
            try:
                native.client.run("owner/model", input={"prompt": "Controlled failure"})
            except expected:
                pass
            else:
                raise AssertionError("Native provider failure missing")
            finally:
                native.close()
    spans = r.memory.get_finished_spans()
    for span in spans[:2]:
        assert span.status.status_code.name == "ERROR"
        assert "traceloop.entity.output" not in span.attributes
    assert [span.attributes["http.response.status_code"] for span in spans[:2]] == [
        429,
        201,
    ]
finally:
    r.close()
