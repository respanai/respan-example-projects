"""Released-SDK fixtures with local capture by default and explicit live/export modes."""

from __future__ import annotations

import atexit
import json
import os
import uuid
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan_instrumentation_langchain import LangChainInstrumentor, add_respan_callback

ROOT_DIR = Path(__file__).resolve().parents[3]
EXPORT = os.getenv("RESPAN_EXPORT", "0") == "1"
LIVE = os.getenv("LANGCHAIN_LIVE", "0") == "1"
if EXPORT or LIVE:
    load_dotenv(
        Path(os.getenv("RESPAN_ENV_FILE", str(ROOT_DIR / ".env"))), override=False
    )
if not LIVE:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
RUN_ID = (
    os.getenv("RESPAN_EXAMPLE_RUN_ID", "").strip()
    or f"langchain-{uuid.uuid4().hex[:12]}"
)
_ACTIVE = []
_EXPORTER = None


class LocalTelemetry:
    def __init__(self, provider):
        self.provider = provider

    def flush(self):
        self.provider.force_flush()


def _finish():
    for telemetry, instrumentor in reversed(_ACTIVE):
        instrumentor.deactivate()
        telemetry.flush()
    if _EXPORTER is not None:
        spans = _EXPORTER.get_finished_spans()
        print(f"LOCAL_TRACE_COUNT={len(spans)}")
        path = os.getenv("LANGCHAIN_CAPTURE_DIR")
        if path:
            target = Path(path)
            target.mkdir(parents=True, exist_ok=True)
            target.joinpath(f"{RUN_ID}-{os.getpid()}.json").write_text(
                json.dumps(
                    [
                        {
                            "name": s.name,
                            "span_id": f"{s.context.span_id:016x}",
                            "trace_id": f"{s.context.trace_id:032x}",
                            "parent_id": f"{s.parent.span_id:016x}"
                            if s.parent
                            else None,
                            "status": s.status.status_code.name,
                            "attributes": dict(s.attributes),
                            "events": [
                                {"name": e.name, "attributes": dict(e.attributes)}
                                for e in s.events
                            ],
                        }
                        for s in spans
                    ],
                    ensure_ascii=False,
                    indent=2,
                )
            )


atexit.register(_finish)


def init_telemetry(app_name: str):
    global _EXPORTER
    if EXPORT:
        from respan_tracing import RespanTelemetry

        key = os.environ["RESPAN_API_KEY"]
        telemetry = RespanTelemetry(
            app_name=app_name,
            api_key=key,
            base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
            is_auto_instrument=False,
            is_batching_enabled=False,
        )
        provider = trace.get_tracer_provider()
    else:
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        telemetry = LocalTelemetry(provider)
    _EXPORTER = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(_EXPORTER))
    instrumentor = LangChainInstrumentor()
    instrumentor.activate()
    _ACTIVE.append((telemetry, instrumentor))
    return telemetry


def tracing_config(name: str, metadata: dict[str, Any] | None = None):
    return add_respan_callback(
        {
            "run_name": name,
            "tags": ["respan-langchain-example", name],
            "metadata": {
                "example": name,
                **(metadata or {}),
                "respan_params": {
                    "trace_group_identifier": f"langchain_{name}.workflow",
                    "custom_identifier": f"{RUN_ID}:{name}",
                    "metadata": {
                        "example": "langchain",
                        "example_run_id": RUN_ID,
                        "run_id": RUN_ID,
                        "workflow_name": f"langchain_{name}.workflow",
                    },
                },
            },
        }
    )


def message_text(message):
    content = getattr(message, "content", None)
    return (
        content
        if isinstance(content, str)
        else json.dumps(content, default=lambda v: type(v).__name__)
    )


@tool
def get_weather(city: str) -> str:
    """Get deterministic weather for a city."""
    return f"It is sunny in {city}."


class ToolCallingFakeMessagesListChatModel(FakeMessagesListChatModel):
    """Real LangChain fake model; bind retains the schemas in invocation params."""

    def bind_tools(self, tools: Any, **kwargs: Any):
        return self.bind(tools=[convert_to_openai_tool(t) for t in tools], **kwargs)


def fake_tool_calling_model(
    *,
    tool_name="get_weather",
    args=None,
    final_text="The tool result has been handled.",
):
    return ToolCallingFakeMessagesListChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": tool_name,
                        "args": args or {"city": "San Francisco"},
                        "id": f"call_{tool_name}",
                    }
                ],
            ),
            AIMessage(content=final_text),
        ]
    )


def _schema_value(schema):
    kind = schema.get("type")
    if kind == "integer":
        return 2010
    if kind == "number":
        return 1.0
    if kind == "boolean":
        return True
    if kind == "array":
        return []
    if kind == "object" or "properties" in schema:
        return {k: _schema_value(v) for k, v in schema.get("properties", {}).items()}
    return (
        "ada@example.com"
        if "email" in schema.get("title", "").lower()
        else "Controlled value"
    )


def provider_response(request):
    """Controlled HTTP/SSE response observed by the real released OpenAI SDK."""
    body = json.loads(request.content)
    if "FAIL_PROVIDER" in json.dumps(body.get("messages")):
        return httpx.Response(
            503,
            json={
                "error": {
                    "message": "controlled provider error",
                    "type": "server_error",
                    "code": "fixture_error",
                }
            },
        )
    message = {"role": "assistant", "content": "Controlled HTTP answer."}
    schema = body.get("response_format", {}).get("json_schema", {}).get("schema")
    tools = body.get("tools") or []
    if schema:
        message["content"] = json.dumps(_schema_value(schema))
    elif tools and body.get("tool_choice"):
        definition = tools[0]["function"]
        message["content"] = ""
        message["tool_calls"] = [
            {
                "id": "fixture-http-call",
                "type": "function",
                "function": {
                    "name": definition["name"],
                    "arguments": json.dumps(
                        _schema_value(definition.get("parameters", {}))
                    ),
                },
            }
        ]
    usage = {
        "prompt_tokens": 11,
        "completion_tokens": 7,
        "total_tokens": 18,
        "prompt_tokens_details": {"cached_tokens": 3},
        "completion_tokens_details": {"reasoning_tokens": 2},
    }
    if body.get("stream"):
        chunks = [
            {
                "id": "fixture-stream",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": "fixture-openai",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": "Controlled "},
                        "finish_reason": None,
                    }
                ],
            },
            {
                "id": "fixture-stream",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": "fixture-openai",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": "SSE answer."},
                        "finish_reason": "stop",
                    }
                ],
            },
            {
                "id": "fixture-stream",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": "fixture-openai",
                "choices": [],
                "usage": usage,
            },
        ]
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content="".join("data: " + json.dumps(c) + "\n\n" for c in chunks)
            + "data: [DONE]\n\n",
        )
    return httpx.Response(
        200,
        json={
            "id": "fixture-http",
            "object": "chat.completion",
            "created": 1,
            "model": "fixture-openai",
            "choices": [
                {
                    "index": 0,
                    "message": message,
                    "finish_reason": "tool_calls"
                    if "tool_calls" in message
                    else "stop",
                }
            ],
            "usage": usage,
        },
    )


def make_openai_chat_model(model_name="gpt-4o-mini"):
    from langchain_openai import ChatOpenAI

    if LIVE:
        return ChatOpenAI(
            model=os.getenv("LANGCHAIN_OPENAI_MODEL", model_name),
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.getenv("OPENAI_BASE_URL"),
            temperature=0,
            max_retries=0,
        )
    return ChatOpenAI(
        model="fixture-openai",
        api_key="fixture-key",
        http_client=httpx.Client(transport=httpx.MockTransport(provider_response)),
        http_async_client=httpx.AsyncClient(
            transport=httpx.MockTransport(provider_response)
        ),
        temperature=0,
        max_retries=0,
    )
