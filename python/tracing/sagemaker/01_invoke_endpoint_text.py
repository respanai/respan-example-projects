import json

from _native import client
from _shared import Runtime

runtime = Runtime("01_text")
try:
    with runtime.workflow():
        c, _, _ = client(
            {
                "generated_text": "native SageMaker text",
                "usage": {"input_tokens": 0, "output_tokens": 2},
            }
        )
        try:
            result = c.invoke_endpoint(
                EndpointName="controlled-endpoint",
                Body=b'{"inputs":"native prompt"}',
                ContentType="application/json",
            )
            body = result["Body"]
            assert body._amount_read == 0
            assert json.loads(body.read())["generated_text"] == "native SageMaker text"
            body.close()
        finally:
            c.close()
finally:
    runtime.close()
