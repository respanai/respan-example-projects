import json

from _native import Native
from _shared import Runtime

r = Runtime("full_payloads")
value = {
    "object": "embedding",
    "embedding": [0.0] * 5001,
    "extra": {"zero": 0, "false": False, "empty": []},
}
n = Native(value)
try:
    with r.workflow():
        body = {
            "messages": [
                {"role": "user", "content": "history-" + str(i)} for i in range(75)
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "controlled",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "api_key": {
                                    "type": "string",
                                    "description": "Schema field name",
                                }
                            },
                        },
                    },
                }
            ],
            "authorization": "Bearer controlled-secret",
            "context_note": 'Authorization: Bearer "controlled-secret"',
            "empty": {},
        }
        result = n.client.run("owner/model", input=body)
        assert result == value
    span = r.memory.get_finished_spans()[0]
    assert len(json.loads(span.attributes["traceloop.entity.output"])) == 5001
    captured = json.loads(span.attributes["traceloop.entity.input"])
    assert len(captured["kwargs"]["input"]["messages"]) == 75
    assert "controlled-secret" not in json.dumps(dict(span.attributes))
finally:
    n.close()
    r.close()
