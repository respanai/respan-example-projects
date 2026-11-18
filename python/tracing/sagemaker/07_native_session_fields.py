from _native import client
from _shared import Runtime

c, _, _ = client(
    {"generated_text": "native session"},
    headers={
        "x-amzn-sagemaker-new-session-id": "controlled-session;Expires=2026-10-05T00:00:00Z",
        "x-amzn-invoked-production-variant": "controlled-variant",
    },
)
if (
    "SessionId"
    not in c.meta.service_model.operation_model("InvokeEndpoint").input_shape.members
):
    c.close()
    print("SKIP: native declared SDK floor has no SessionId")
    raise SystemExit(0)
runtime = Runtime("07_sessions")
try:
    with runtime.workflow():
        result = c.invoke_endpoint(
            EndpointName="controlled-endpoint",
            SessionId="NEW_SESSION",
            Body=b'{"inputs":"native"}',
            ContentType="application/json",
        )
        assert result["Body"].read()
        result["Body"].close()
finally:
    c.close()
    runtime.close()
