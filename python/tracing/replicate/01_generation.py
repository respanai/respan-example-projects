from _native import Native
from _shared import Runtime

r = Runtime("generation")
n = Native(["controlled ", "completion"])
try:
    with r.workflow():
        result = n.client.run(
            "owner/model",
            input={
                "prompt": "Explain observability",
                "temperature": 0,
                "flag": False,
                "empty": [],
            },
        )
        assert result == ["controlled ", "completion"]
finally:
    n.close()
    r.close()
