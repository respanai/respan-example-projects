import json

from _native import client, frame
from _shared import Runtime
from botocore.eventstream import EventStream

runtime = Runtime("03_stream")
frames = [
    {
        "choices": [
            {
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "content": "native ",
                    "tool_calls": [
                        {
                            "index": 0,
                            "id": "controlled-stream-id",
                            "type": "function",
                            "function": {"name": "lookup", "arguments": '{"false":'},
                        }
                    ],
                },
            }
        ]
    },
    {
        "choices": [
            {
                "index": 0,
                "delta": {
                    "content": "stream",
                    "tool_calls": [
                        {"index": 0, "function": {"arguments": 'false,"zero":0}'}}
                    ],
                },
            }
        ],
        "usage": {"input_tokens": 0, "output_tokens": 2},
    },
]
data = b"".join((json.dumps(v) + "\n").encode() for v in frames)
wire = frame(data[:19]) + frame(data[19:31]) + frame(data[31:])
try:
    with runtime.workflow():
        c, _, _ = client(events=wire)
        try:
            result = c.invoke_endpoint_with_response_stream(
                EndpointName="controlled-endpoint",
                Body=b'{"messages":[{"role":"user","content":"native"}]}',
                ContentType="application/json",
            )
            assert type(result["Body"]) is EventStream
            assert b"".join(e["PayloadPart"]["Bytes"] for e in result["Body"]) == data
            result["Body"].close()
        finally:
            c.close()
finally:
    runtime.close()
