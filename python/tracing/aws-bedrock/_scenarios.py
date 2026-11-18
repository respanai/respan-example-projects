"""Controlled cases use native HTTP deserialization and AWS event-stream CRCs."""

from __future__ import annotations

import json
import os

from _shared import create_bedrock_client, event_frames, frame, get_model_id, transport
from botocore.eventstream import EventStream
from botocore.exceptions import ClientError
from botocore.response import StreamingBody
from opentelemetry import context
from opentelemetry.instrumentation.utils import _SUPPRESS_INSTRUMENTATION_KEY
from opentelemetry.semconv_ai import SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY

PARAMS = {
    "modelId": "anthropic.controlled",
    "messages": [{"role": "user", "content": [{"text": "controlled prompt"}]}],
}
INVOKE = {
    "modelId": "anthropic.controlled",
    "body": json.dumps(
        {"messages": [{"role": "user", "content": "controlled prompt"}]}
    ),
    "contentType": "application/json",
}


def converse_payload():
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {"text": "controlled hello"},
                    {
                        "reasoningContent": {
                            "reasoningText": {
                                "text": "controlled reasoning",
                                "signature": "controlled-signature",
                            }
                        }
                    },
                ],
            }
        },
        "stopReason": "end_turn",
        "usage": {
            "inputTokens": 0,
            "outputTokens": 2,
            "totalTokens": 2,
            "cacheReadInputTokens": 0,
            "cacheWriteInputTokens": 3,
        },
        "metrics": {"latencyMs": 1},
    }


def available(client, method):
    if hasattr(client, method):
        return True
    print(f"SKIP: {method} is unavailable in this released boto3 service model")
    return False


def invoke_model(provider):
    client = create_bedrock_client()
    payload = {
        "content": [{"type": "text", "text": "controlled hello"}],
        "usage": {"input_tokens": 0, "output_tokens": 2},
    }
    transport(client, payload)
    body = client.invoke_model(**INVOKE)["body"]
    assert type(body) is StreamingBody and body.tell() == 0
    assert body.read(0) == b""
    result = json.loads(body.read())
    body.close()
    client.close()
    assert result == payload
    return result["content"][0]["text"]


def converse(provider):
    client = create_bedrock_client()
    if not available(client, "converse"):
        return "skipped"
    transport(client, converse_payload())
    response = client.converse(**PARAMS)
    client.close()
    return response["output"]["message"]["content"][0]["text"]


def converse_stream(provider):
    client = create_bedrock_client()
    if not available(client, "converse_stream"):
        return "skipped"
    events = [
        ("messageStart", {"role": "assistant"}),
        (
            "contentBlockStart",
            {
                "contentBlockIndex": 0,
                "start": {"toolUse": {"toolUseId": "tool-1", "name": "weather"}},
            },
        ),
        (
            "contentBlockDelta",
            {
                "contentBlockIndex": 0,
                "delta": {"toolUse": {"input": '{"city":"Shanghai",'}},
            },
        ),
        (
            "contentBlockDelta",
            {
                "contentBlockIndex": 0,
                "delta": {"toolUse": {"input": '"zero":0,"false":false}'}},
            },
        ),
        ("contentBlockDelta", {"contentBlockIndex": 1, "delta": {"text": "hello"}}),
        (
            "contentBlockDelta",
            {
                "contentBlockIndex": 2,
                "delta": {"reasoningContent": {"text": "controlled reasoning"}},
            },
        ),
        ("messageStop", {"stopReason": "tool_use"}),
        (
            "metadata",
            {
                "usage": {
                    "inputTokens": 0,
                    "outputTokens": 2,
                    "totalTokens": 2,
                    "cacheReadInputTokens": 0,
                },
                "metrics": {"latencyMs": 1},
            },
        ),
    ]
    transport(client, event_frames(events), event_stream=True)
    stream = client.converse_stream(**PARAMS)["stream"]
    assert type(stream) is EventStream
    parsed = list(stream)
    stream.close()
    client.close()
    assert len(parsed) == len(events)
    return "tool fragments, reasoning, zero and cache usage"


def converse_tool(provider):
    client = create_bedrock_client()
    if not available(client, "converse"):
        return "skipped"
    payload = converse_payload()
    payload["output"]["message"]["content"] = [
        {
            "toolUse": {
                "toolUseId": "tool-2",
                "name": "weather",
                "input": {"city": "Shanghai", "zero": 0, "false": False, "empty": ""},
            }
        }
    ]
    params = dict(PARAMS)
    params["messages"] = [
        {
            "role": "assistant",
            "content": [
                {
                    "toolUse": {
                        "toolUseId": "old-tool",
                        "name": "weather",
                        "input": {"city": "Paris"},
                    }
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "toolResult": {
                        "toolUseId": "old-tool",
                        "content": [{"json": {"temperature": 0, "sunny": False}}],
                    }
                },
                {"text": "Next city"},
            ],
        },
    ]
    params["toolConfig"] = {
        "tools": [
            {
                "toolSpec": {
                    "name": "weather",
                    "description": "Controlled weather tool",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string"},
                                "api_key": {
                                    "type": "string",
                                    "default": "controlled-secret",
                                },
                            },
                        }
                    },
                }
            }
        ]
    }
    transport(client, payload)
    result = client.converse(**params)
    client.close()
    assert result["output"]["message"]["content"][0]["toolUse"]["toolUseId"] == "tool-2"
    return "history, tool result, full schema and new tool call"


def converse_error(provider):
    client = create_bedrock_client()
    if not available(client, "converse"):
        return "skipped"
    transport(
        client,
        {"message": 'password="controlled-secret"', "__type": "ValidationException"},
        status=400,
    )
    try:
        client.converse(**PARAMS)
    except ClientError as error:
        assert error.response["ResponseMetadata"]["HTTPStatusCode"] == 400
    else:
        raise AssertionError("native error expected")
    finally:
        client.close()
    return "native controlled validation error"


def invoke_stream(provider):
    client = create_bedrock_client()
    events = [
        {"type": "message_start", "message": {"usage": {"input_tokens": 0}}},
        {
            "type": "content_block_start",
            "index": 0,
            "content_block": {
                "type": "tool_use",
                "id": "tool-3",
                "name": "weather",
                "input": {},
            },
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {
                "type": "input_json_delta",
                "partial_json": '{"city":"Shanghai","zero":0}',
            },
        },
        {
            "type": "content_block_delta",
            "index": 1,
            "delta": {"type": "text_delta", "text": "hello"},
        },
        {"type": "message_delta", "usage": {"output_tokens": 2}},
    ]
    transport(client, event_frames(events, invoke=True), event_stream=True)
    stream = client.invoke_model_with_response_stream(**INVOKE)["body"]
    assert type(stream) is EventStream and len(list(stream)) == len(events)
    stream.close()
    client.close()
    return "native InvokeModel event frames"


def embedding(provider):
    client = create_bedrock_client()
    vector = [float(i) for i in range(5001)]
    transport(client, {"embedding": vector, "inputTextTokenCount": 0})
    body = client.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        body=json.dumps({"inputText": "controlled text"}),
    )["body"]
    assert len(json.loads(body.read())["embedding"]) == 5001
    body.close()
    client.close()
    return "5001-dimensional vector and zero input usage"


def privacy(provider):
    for key in (
        "override_enable_content_tracing",
        _SUPPRESS_INSTRUMENTATION_KEY,
        SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY,
    ):
        client = create_bedrock_client()
        transport(
            client,
            {"content": [{"type": "text", "text": "private controlled content"}]},
        )
        token = context.attach(
            context.set_value(key, key != "override_enable_content_tracing")
        )
        try:
            body = client.invoke_model(**INVOKE)["body"]
            assert body.read()
            body.close()
        finally:
            context.detach(token)
            client.close()
    client = create_bedrock_client()
    transport(client, {"content": [{"type": "text", "text": "late private content"}]})
    with provider.get_tracer("bedrock.examples").start_as_current_span(
        "privacy-parent"
    ) as parent:
        body = client.invoke_model(**INVOKE)["body"]
        parent.set_attribute("traceloop.enable_content_tracing", False)
    assert body.read()
    body.close()
    client.close()
    return "initial policy, both suppression keys and finished-parent veto"


def stream_error(provider):
    client = create_bedrock_client()
    if not available(client, "converse_stream"):
        return "skipped"
    transport(
        client,
        frame(
            "validationException",
            {"message": "controlled stream error"},
            message_type="exception",
        ),
        event_stream=True,
    )
    stream = client.converse_stream(**PARAMS)["stream"]
    try:
        list(stream)
    except ClientError:
        pass
    else:
        raise AssertionError("native event-stream error expected")
    finally:
        stream.close()
        client.close()
    return "native event-stream error"


def body_lifecycle(provider):
    for mode in ("readinto", "context", "partial-close"):
        client = create_bedrock_client()
        raw = transport(
            client, {"content": [{"type": "text", "text": "body lifecycle"}]}
        )
        body = client.invoke_model(**INVOKE)["body"]
        if mode == "readinto":
            if not hasattr(body, "readinto"):
                print("SKIP: StreamingBody.readinto is absent from this released SDK")
                body.close()
                client.close()
                continue
            buffer = bytearray(7)
            while body.readinto(buffer):
                pass
        elif mode == "context":
            with body as entered:
                assert entered is raw.raw
                assert entered.read()
        else:
            assert body.read(2)
        body.close()
        assert raw.raw.closed
        client.close()
    return "readinto, native context and partial close"


def live_optional(provider):
    if os.getenv("AWS_BEDROCK_LIVE") != "1":
        return (
            "SKIP real AWS invocation; set AWS_BEDROCK_LIVE=1 and AWS_BEDROCK_MODEL_ID"
        )
    if not os.getenv("AWS_BEDROCK_MODEL_ID"):
        raise RuntimeError("AWS_BEDROCK_MODEL_ID is required for a live invocation")
    client = create_bedrock_client(live=True)
    try:
        result = client.converse(
            modelId=get_model_id(),
            messages=PARAMS["messages"],
            inferenceConfig={"maxTokens": 32},
        )
        return result["stopReason"]
    finally:
        client.close()
