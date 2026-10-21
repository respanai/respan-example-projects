import json

from _native import client
from _shared import Runtime

runtime = Runtime("05_embedding")
payload = {
    "object": "list",
    "model": "controlled-embedding",
    "data": [{"object": "embedding", "index": 0, "embedding": list(range(5001))}],
    "usage": {"input_tokens": 0},
}
try:
    with runtime.workflow():
        c, _, _ = client(payload)
        try:
            result = c.invoke_endpoint(
                EndpointName="controlled-endpoint",
                Body=b'{"input":["native document"],"model":"controlled-embedding"}',
                ContentType="application/json",
            )
            assert json.loads(result["Body"].read()) == payload
            result["Body"].close()
        finally:
            c.close()
finally:
    runtime.close()
