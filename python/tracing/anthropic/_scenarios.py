"""Real released Anthropic clients parse deterministic HTTP and SSE fixtures."""

from __future__ import annotations

import asyncio
import json
import os

import anthropic
from opentelemetry import context, trace
from opentelemetry.context import _SUPPRESS_INSTRUMENTATION_KEY

try:
    import httpx2 as httpx
except ImportError:
    import httpx

REQUEST = {
    "model": "claude-controlled",
    "max_tokens": 32,
    "messages": [{"role": "user", "content": "Controlled Anthropic fixture"}],
}


def message(text="Controlled reply", content=None):
    return {
        "id": "msg_fixture",
        "type": "message",
        "role": "assistant",
        "model": "claude-controlled",
        "content": content if content is not None else [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 7, "output_tokens": 3, "cache_read_input_tokens": 0},
    }


def sse(events):
    return "".join(
        f"event: {name}\ndata: {json.dumps(data)}\n\n" for name, data in events
    ).encode()


def message_frames(error=False, text="Controlled reply"):
    events = [
        (
            "message_start",
            {
                "type": "message_start",
                "message": {
                    **message(),
                    "content": [],
                    "stop_reason": None,
                    "usage": {"input_tokens": 7, "output_tokens": 0},
                },
            },
        ),
        (
            "content_block_start",
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
        ),
        (
            "content_block_delta",
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": text},
            },
        ),
    ]
    events += (
        [
            (
                "error",
                {
                    "type": "error",
                    "error": {
                        "type": "overloaded_error",
                        "message": "Controlled stream failure",
                    },
                },
            )
        ]
        if error
        else [
            ("content_block_stop", {"type": "content_block_stop", "index": 0}),
            (
                "message_delta",
                {
                    "type": "message_delta",
                    "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                    "usage": {"output_tokens": 3},
                },
            ),
            ("message_stop", {"type": "message_stop"}),
        ]
    )
    return sse(events)


def client(*, response=None, handler=None, asynchronous=False):
    def send(request):
        if handler:
            return handler(request)
        return (
            httpx.Response(
                200,
                content=message_frames(
                    text=response["content"][0]["text"]
                    if response
                    else "Controlled reply"
                ),
                headers={"content-type": "text/event-stream"},
            )
            if json.loads(request.content).get("stream")
            else httpx.Response(200, json=response or message())
        )

    cls = anthropic.AsyncAnthropic if asynchronous else anthropic.Anthropic
    http = httpx.AsyncClient if asynchronous else httpx.Client
    return cls(
        api_key="controlled-fixture",
        http_client=http(transport=httpx.MockTransport(send)),
        max_retries=0,
    )


def basic(provider):
    with client() as c:
        result = c.messages.create(**REQUEST)
        beta = c.beta.messages.create(
            **REQUEST,
            betas=["controlled-beta"],
            extra_body={
                "thinking": {"type": "disabled"},
                "output_config": {
                    "format": {
                        "type": "json_schema",
                        "schema": {
                            "type": "object",
                            "properties": {"text": {"type": "string"}},
                        },
                    }
                },
            },
        )
        assert result.content[0].text == beta.content[0].text == "Controlled reply"
    return {"stable_and_beta": True}


def streaming(provider):
    skipped = []
    with client() as c:
        for name, api in (("stable", c.messages), ("beta", c.beta.messages)):
            with api.create(**REQUEST, stream=True) as stream:
                assert isinstance(stream, anthropic.Stream)
                assert len(list(stream)) == 6
            assert stream.response.is_closed
            if hasattr(api, "stream"):
                with api.stream(**REQUEST) as helper:
                    assert "".join(helper.text_stream) == "Controlled reply"
                    assert (
                        helper.get_final_message().content[0].text == "Controlled reply"
                    )
                assert helper.response.is_closed
            else:
                skipped.append(name + " native helper unavailable")
        with c.messages.stream(**REQUEST) as partial:
            next(partial)
        assert partial.response.is_closed
        first = c.messages.create(**REQUEST, stream=True)
        second = c.messages.create(**REQUEST, stream=True)
        with first as stream:
            assert len(list(stream)) == 6
        with second as stream:
            assert len(list(stream)) == 6
    return {
        "native_streams": True,
        "optional_skips": skipped,
        "partial_close_without_drain": True,
    }


def tool_round(provider):
    block = {
        "type": "tool_use",
        "id": "toolu_fixture",
        "name": "lookup_weather",
        "input": {
            "city": "Tokyo",
            "values": list(range(5001)),
            "enabled": False,
            "zero": 0,
            "empty": [],
        },
    }
    definition = {
        "name": "lookup_weather",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "api_key": {"type": "string", "default": "controlled-secret"},
            },
        },
    }
    with client(
        response=message(
            content=[
                {
                    "type": "thinking",
                    "thinking": "Controlled reasoning",
                    "signature": "signed-fixture",
                },
                block,
            ]
        )
    ) as c:
        first = c.messages.create(**REQUEST, tools=[definition])
        assert first.content[1].id == "toolu_fixture"
    history = [
        *REQUEST["messages"],
        {"role": "assistant", "content": [block]},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_fixture",
                    "content": [
                        {"type": "text", "text": "Sunny; zero=0, enabled=false"}
                    ],
                    "is_error": False,
                }
            ],
        },
    ]
    with client() as c:
        assert (
            c.messages.create(**{**REQUEST, "messages": history, "tools": [definition]})
            .content[0]
            .text
            == "Controlled reply"
        )
    return {
        "tool_id": "toolu_fixture",
        "vector_length": 5001,
        "history": True,
        "local_tool_execution_claimed": False,
    }


def expected_error(provider):
    def send(request):
        return (
            httpx.Response(
                200,
                content=message_frames(error=True),
                headers={"content-type": "text/event-stream"},
            )
            if json.loads(request.content).get("stream")
            else httpx.Response(
                404,
                json={
                    "type": "error",
                    "error": {
                        "type": "not_found_error",
                        "message": "Controlled missing model",
                    },
                },
            )
        )

    statuses = []
    with client(handler=send) as c:
        for streaming in (False, True):
            try:
                if streaming:
                    with c.messages.create(**REQUEST, stream=True) as stream:
                        list(stream)
                else:
                    c.messages.create(**REQUEST)
            except anthropic.APIStatusError as exc:
                statuses.append(exc.status_code)
            else:
                raise AssertionError("Expected native provider error")
    return {"native_error_http_statuses": statuses}


def async_case(provider):
    async def run():
        skips = []
        async with client(asynchronous=True) as c:
            for name, api in (("stable", c.messages), ("beta", c.beta.messages)):
                assert (await api.create(**REQUEST)).content[
                    0
                ].text == "Controlled reply"
                async with await api.create(**REQUEST, stream=True) as stream:
                    assert len([event async for event in stream]) == 6
                if hasattr(api, "stream"):
                    async with api.stream(**REQUEST) as helper:
                        assert (
                            "".join([text async for text in helper.text_stream])
                            == "Controlled reply"
                        )
                        assert (await helper.get_final_message()).content[
                            0
                        ].text == "Controlled reply"
                else:
                    skips.append(name + " native helper unavailable")
        return {"async_native_types": True, "optional_skips": skips}

    return asyncio.run(run())


def privacy(provider):
    parent = trace.get_current_span()
    token = context.attach(context.set_value("respan_enable_content_tracing", False))
    try:
        with client() as c:
            c.messages.create(**REQUEST)
    finally:
        context.detach(token)
    with client() as c, c.messages.create(**REQUEST, stream=True) as stream:
        next(stream)
        token = context.attach(
            context.set_value("respan_enable_content_tracing", False)
        )
        context.detach(token)
        list(stream)
    token = context.attach(context.set_value("trace_content", False))
    try:
        with client() as c:
            c.messages.create(**REQUEST)
    finally:
        context.detach(token)
    with client() as c, c.messages.create(**REQUEST, stream=True) as stream:
        next(stream)
        parent.set_attribute("trace_content", False)
        list(stream)
    token = context.attach(context.set_value(_SUPPRESS_INSTRUMENTATION_KEY, True))
    try:
        with client() as c:
            c.messages.create(**REQUEST)
    finally:
        context.detach(token)
    return {
        "initial_and_late_veto": True,
        "canonical_and_pre_detach_veto": True,
        "suppressed_native_call": True,
    }


def managed_sessions(provider):
    with client() as c:
        if not hasattr(c.beta, "sessions"):
            return {
                "optional_skip": "managed session API not present in this released SDK"
            }
    events = [
        (
            "user.message",
            {
                "type": "user.message",
                "id": "evt_user",
                "content": [{"type": "text", "text": "Controlled agent input"}],
            },
        ),
        (
            "agent.tool_use",
            {
                "type": "agent.tool_use",
                "id": "evt_tool",
                "name": "lookup_weather",
                "input": {"city": "Tokyo"},
            },
        ),
        (
            "agent.message",
            {
                "type": "agent.message",
                "id": "evt_reply",
                "content": [{"type": "text", "text": "Controlled agent output"}],
            },
        ),
        (
            "span.model_request_end",
            {
                "type": "span.model_request_end",
                "id": "evt_usage",
                "model_usage": {"input_tokens": 5, "output_tokens": 2},
            },
        ),
        (
            "session.status_idle",
            {
                "type": "session.status_idle",
                "id": "evt_idle",
                "stop_reason": {"type": "end_turn"},
            },
        ),
    ]

    def send(request):
        return httpx.Response(
            200, content=sse(events), headers={"content-type": "text/event-stream"}
        )

    with (
        client(handler=send) as c,
        c.beta.sessions.events.stream("session_controlled") as stream,
    ):
        assert len(list(stream)) == 5

    async def run():
        async with (
            client(handler=send, asynchronous=True) as c,
            await c.beta.sessions.events.stream("session_controlled") as stream,
        ):
            assert len([event async for event in stream]) == 5

    asyncio.run(run())
    return {"native_sync_async_managed_events": True, "deployed_agent_resources": False}


def typed_parse(provider):
    from pydantic import BaseModel

    class Answer(BaseModel):
        text: str

    skips = []
    with client(response=message(text='{"text":"Typed controlled reply"}')) as c:
        for name, api in (("stable", c.messages), ("beta", c.beta.messages)):
            if hasattr(api, "parse"):
                result = api.parse(**REQUEST, output_format=Answer)
                assert isinstance(result.parsed_output, Answer)
                assert result.parsed_output.text == "Typed controlled reply"
                with api.stream(**REQUEST, output_format=Answer) as stream:
                    list(stream)
                    final = stream.get_final_message()
                    assert isinstance(final.parsed_output, Answer)
                    assert final.parsed_output.text == "Typed controlled reply"
            else:
                skips.append(name + " parse unavailable")
    return {"native_typed_parse": not skips, "optional_skips": skips}


def live_provider(provider):
    key = os.environ["ANTHROPIC_API_KEY"]
    model = os.environ["ANTHROPIC_MODEL"]
    with anthropic.Anthropic(api_key=key) as c:
        response = c.messages.create(
            model=model,
            max_tokens=16,
            messages=[{"role": "user", "content": "Reply with the word tracing."}],
        )
    return {"native_provider_response_type": type(response).__name__}


SCENARIOS = {
    "basic": basic,
    "streaming": streaming,
    "tool_round": tool_round,
    "expected_error": expected_error,
    "async": async_case,
    "privacy": privacy,
    "managed_sessions": managed_sessions,
    "typed_parse": typed_parse,
    "live_provider": live_provider,
}
