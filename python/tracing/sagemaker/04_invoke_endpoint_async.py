from _native import client
from _shared import Runtime

runtime = Runtime("04_async")
try:
    with runtime.workflow():
        c, _, _ = client(
            {},
            status=202,
            headers={
                "x-amzn-sagemaker-inference-id": "controlled-inference",
                "x-amzn-sagemaker-outputlocation": "s3://controlled/output",
                "x-amzn-sagemaker-failurelocation": "s3://controlled/failure",
            },
        )
        try:
            result = c.invoke_endpoint_async(
                EndpointName="controlled-endpoint",
                InputLocation="s3://controlled/input",
                ContentType="application/json",
            )
            assert result["ResponseMetadata"]["HTTPStatusCode"] == 202
        finally:
            c.close()
finally:
    runtime.close()
