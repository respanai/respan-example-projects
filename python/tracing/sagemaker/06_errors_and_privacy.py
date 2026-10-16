from _native import client, frame
from _shared import Runtime
from botocore.exceptions import ClientError, EventStreamError
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

runtime = Runtime("06_errors_privacy")
try:
    with runtime.workflow():
        c, _, _ = client(
            {"Message": "controlled error"},
            status=429,
            headers={"x-amzn-errortype": "ThrottlingException"},
        )
        try:
            try:
                c.invoke_endpoint(
                    EndpointName="controlled-endpoint",
                    Body=b'{"inputs":"native"}',
                    ContentType="application/json",
                )
            except ClientError as error:
                assert error.response["ResponseMetadata"]["HTTPStatusCode"] == 429
            else:
                raise AssertionError("native error absent")
        finally:
            c.close()
        c, _, _ = client(
            events=frame(b'{"token":{"text":"native partial"}}\n')
            + frame(
                b'{"Message":"controlled stream error"}',
                kind="ModelStreamError",
                message_type="exception",
            )
        )
        try:
            result = c.invoke_endpoint_with_response_stream(
                EndpointName="controlled-endpoint",
                Body=b'{"inputs":"native"}',
                ContentType="application/json",
            )
            try:
                list(result["Body"])
            except EventStreamError:
                pass
            else:
                raise AssertionError("native stream error absent")
            result["Body"].close()
        finally:
            c.close()
        c, _, _ = client({"generated_text": "PRIVATE result"})
        try:
            result = c.invoke_endpoint(
                EndpointName="controlled-endpoint",
                Body=b'{"inputs":"PRIVATE prompt"}',
                ContentType="application/json",
            )
            token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
            context.detach(token)
            result["Body"].read()
            result["Body"].close()
        finally:
            c.close()
finally:
    runtime.close()
