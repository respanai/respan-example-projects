"""Released-SDK loopback fixtures; explicit opt-in for trace export."""

from __future__ import annotations

import inspect
import json
import os
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from functools import wraps
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, NamedTuple

import openlit
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from openlit.semcov import SemanticConvention
from opentelemetry import trace
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv._incubating.attributes.gen_ai_attributes import (
    GEN_AI_OPERATION_NAME,
    GEN_AI_TOOL_NAME,
)
from opentelemetry.semconv_ai import SpanAttributes
from respan_instrumentation_openlit import OpenLITInstrumentor
from respan_instrumentation_openlit._policy import allowed
from respan_sdk.constants.span_attributes import RESPAN_METADATA

EXAMPLE_DIR = Path(__file__).resolve().parent
EXAMPLE_REPO_ROOT = EXAMPLE_DIR.parents[2]
DEFAULT_MODEL = "gpt-4.1-mini"
EXPORT = os.getenv("RESPAN_EXPORT", "0") == "1"
if EXPORT or os.getenv("RESPAN_OPENLIT_LIVE") == "1":
    load_dotenv(
        Path(os.getenv("RESPAN_ENV_FILE", str(EXAMPLE_REPO_ROOT / ".env"))),
        override=False,
    )
RUN_ID = os.getenv("RESPAN_EXAMPLE_RUN_ID") or "openlit-" + uuid.uuid4().hex[:12]


def _load_env_file(path):
    load_dotenv(path, override=False)


def require_run_id():
    if (
        RUN_ID != RUN_ID.strip()
        or any(c in RUN_ID for c in "\r\n")
        or len(RUN_ID.encode()) > 160
    ):
        raise RuntimeError(
            "RESPAN_EXAMPLE_RUN_ID must be an exact marker of at most160 bytes"
        )
    return RUN_ID


def example_metadata(scenario):
    return {
        "run_id": require_run_id(),
        "example_run_id": require_run_id(),
        "framework": "openlit",
        "scenario": scenario,
        "example": scenario,
        "example_set": "python/tracing/openlit",
    }


class Marker(SpanProcessor):
    def __init__(self, scenario):
        self.metadata = example_metadata(scenario)

    def on_start(self, span, parent_context=None):
        span.set_attribute(RESPAN_METADATA, json.dumps(self.metadata))
        for key, value in self.metadata.items():
            span.set_attribute(RESPAN_METADATA + "." + key, value)

    def on_end(self, span):
        pass

    def shutdown(self):
        pass

    def force_flush(self, timeout_millis=30000):
        return True


class Telemetry:
    def __init__(self, provider, owner, exporter):
        self.provider, self.owner, self.exporter = provider, owner, exporter

    def flush(self):
        self.provider.force_flush()

    def shutdown(self):
        self.provider.force_flush()
        self.owner.deactivate()
        spans = self.exporter.get_finished_spans()
        print("LOCAL_TRACE_COUNT=" + str(len(spans)))
        directory = os.getenv("OPENLIT_CAPTURE_DIR")
        if directory:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            path.joinpath(f"{RUN_ID}-{os.getpid()}.json").write_text(
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
                    indent=2,
                )
            )
        self.provider.shutdown()


def create_respan(scenario, *, capture_content=True):
    if EXPORT:
        from respan_tracing import RespanTelemetry

        RespanTelemetry(
            app_name="openlit-" + scenario,
            api_key=os.environ["RESPAN_API_KEY"],
            base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
            is_auto_instrument=False,
            is_batching_enabled=False,
        )
        provider = trace.get_tracer_provider()
    else:
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
    exporter = InMemorySpanExporter()
    provider.add_span_processor(Marker(scenario))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    owner = OpenLITInstrumentor(
        capture_content=capture_content, max_content_length=4096
    )
    owner.activate()
    return Telemetry(provider, owner, exporter)


@contextmanager
def example_scope(scenario):
    yield


def finish_respan(respan):
    try:
        respan.flush()
    finally:
        respan.shutdown()


def _entity(kind, name):
    def decorate(function):
        @wraps(function)
        def run(*args, **kwargs):
            with openlit.start_trace(name) as native:
                native.set_metadata(
                    {
                        GEN_AI_OPERATION_NAME: "execute_tool"
                        if kind == "tool"
                        else "invoke_workflow",
                        GEN_AI_TOOL_NAME
                        if kind == "tool"
                        else SemanticConvention.GEN_AI_WORKFLOW_NAME: name,
                    }
                )
                if allowed(trace.get_current_span()):
                    actual = dict(
                        inspect.signature(function).bind(*args, **kwargs).arguments
                    )
                    native.set_metadata(
                        {
                            SpanAttributes.TRACELOOP_ENTITY_INPUT: json.dumps(
                                {"name": name, "arguments": actual}
                                if kind == "tool"
                                else actual
                            )
                        }
                    )
                result = function(*args, **kwargs)
                if allowed(trace.get_current_span()):
                    native.set_metadata(
                        {SpanAttributes.TRACELOOP_ENTITY_OUTPUT: json.dumps(result)}
                    )
                return result

        return run

    return decorate


def workflow(*, name):
    return _entity("workflow", name)


def tool(*, name):
    return _entity("tool", name)


class ProviderConfig(NamedTuple):
    api_key: str
    base_url: str | None
    model: str
    embedding_model: str
    live: bool


def _chat_payload(request: dict[str, Any]) -> dict[str, Any]:
    model = str(request.get("model") or DEFAULT_MODEL)
    messages = request.get("messages") or []
    if request.get("tools") and request.get("tool_choice"):
        message: dict[str, Any] = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_openlit_weather",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": json.dumps({"city": "Tokyo"}),
                    },
                }
            ],
        }
        finish_reason = "tool_calls"
    elif any(
        isinstance(message, dict) and message.get("role") == "tool"
        for message in messages
    ):
        message = {"role": "assistant", "content": "Tokyo is sunny and 22 C."}
        finish_reason = "stop"
    else:
        message = {"role": "assistant", "content": "OpenLIT deterministic reply."}
        finish_reason = "stop"
    return {
        "id": f"chatcmpl-openlit-{time.time_ns()}",
        "object": "chat.completion",
        "created": 1_700_000_000,
        "model": model,
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 7,
            "total_tokens": 19,
            "prompt_tokens_details": {"cached_tokens": 0},
            "completion_tokens_details": {"reasoning_tokens": 0},
        },
    }


def _response_payload(prompt: str, *, status: str = "completed") -> dict[str, Any]:
    text = (
        '{"city":"Paris"}'
        if prompt == "typed-city"
        else "OpenLIT Responses deterministic reply."
    )
    return {
        "id": f"resp-openlit-{time.time_ns()}",
        "object": "response",
        "created_at": 1_700_000_000.0,
        "model": DEFAULT_MODEL,
        "output": (
            [
                {
                    "id": "msg_openlit_response",
                    "type": "message",
                    "status": "completed",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": text, "annotations": []}
                    ],
                }
            ]
            if status == "completed"
            else []
        ),
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "tools": [],
        "status": status,
        "usage": {
            "input_tokens": 6,
            "input_tokens_details": {
                "cached_tokens": 0,
                "cache_write_tokens": 0,
            },
            "output_tokens": 4,
            "output_tokens_details": {"reasoning_tokens": 0},
            "total_tokens": 10,
        },
        "metadata": {"bounded_prompt_length": str(len(prompt))},
    }


class _MockHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        del format, args

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0") or "0")
        return json.loads(self.rfile.read(length)) if length else {}

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse(self, events: list[dict[str, Any]], *, named: bool = False) -> None:
        body = ""
        for event in events:
            if named:
                body += f"event: {event['type']}\n"
            body += f"data: {json.dumps(event)}\n\n"
        body += "data: [DONE]\n\n"
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        try:
            self.wfile.write(encoded)
        except BrokenPipeError:
            pass

    def do_POST(self) -> None:
        request = self._read_json()
        if self.path.endswith("/embeddings"):
            self._send_json(
                200,
                {
                    "object": "list",
                    "model": str(request.get("model") or "text-embedding-3-small"),
                    "data": [
                        {
                            "object": "embedding",
                            "index": 0,
                            "embedding": [i / 5000 for i in range(5000)],
                        }
                    ],
                    "usage": {"prompt_tokens": 4, "total_tokens": 4},
                },
            )
            return
        if self.path.endswith("/responses"):
            prompt = str(request.get("input") or "")
            if request.get("stream"):
                completed = _response_payload(prompt)
                events = [
                    {
                        "type": "response.created",
                        "sequence_number": 0,
                        "response": {
                            **_response_payload(prompt, status="in_progress"),
                            "usage": None,
                        },
                    },
                    {
                        "type": "response.output_text.delta",
                        "sequence_number": 1,
                        "item_id": "msg_openlit_response",
                        "output_index": 0,
                        "content_index": 0,
                        "delta": "OpenLIT Responses deterministic reply.",
                        "logprobs": [],
                    },
                    {
                        "type": "response.completed",
                        "sequence_number": 2,
                        "response": completed,
                    },
                ]
                self._send_sse(events, named=True)
            else:
                self._send_json(200, _response_payload(prompt))
            return
        if not self.path.endswith("/chat/completions"):
            self._send_json(404, {"error": {"message": "not found"}})
            return
        messages = request.get("messages") or []
        prompt = str(messages[0].get("content") if messages else "")
        if prompt == "expected-rate-limit":
            self._send_json(
                429,
                {
                    "error": {
                        "message": "deterministic rate limit",
                        "type": "rate_limit_error",
                    }
                },
            )
            return
        if request.get("stream"):
            chunks = [
                {
                    "id": "chatcmpl-openlit-stream",
                    "object": "chat.completion.chunk",
                    "created": 1_700_000_000,
                    "model": str(request.get("model") or DEFAULT_MODEL),
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": "OpenLIT "},
                            "finish_reason": None,
                        }
                    ],
                },
                {
                    "id": "chatcmpl-openlit-stream",
                    "object": "chat.completion.chunk",
                    "created": 1_700_000_000,
                    "model": str(request.get("model") or DEFAULT_MODEL),
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": "stream reply."},
                            "finish_reason": "stop",
                        }
                    ],
                },
                {
                    "id": "chatcmpl-openlit-stream",
                    "object": "chat.completion.chunk",
                    "created": 1_700_000_000,
                    "model": str(request.get("model") or DEFAULT_MODEL),
                    "choices": [],
                    "usage": {
                        "prompt_tokens": 7,
                        "completion_tokens": 11,
                        "total_tokens": 18,
                    },
                },
            ]
            self._send_sse(chunks)
            return
        self._send_json(200, _chat_payload(request))


@contextmanager
def provider_config(*, force_mock: bool = False) -> Iterator[ProviderConfig]:
    live = not force_mock and os.getenv("RESPAN_OPENLIT_LIVE") == "1"
    if live:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("RESPAN_OPENLIT_LIVE=1 requires OPENAI_API_KEY.")
        yield ProviderConfig(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=os.getenv("RESPAN_OPENLIT_MODEL", DEFAULT_MODEL),
            embedding_model=os.getenv(
                "RESPAN_OPENLIT_EMBEDDING_MODEL", "text-embedding-3-small"
            ),
            live=True,
        )
        return

    server = ThreadingHTTPServer(("127.0.0.1", 0), _MockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield ProviderConfig(
            api_key="local-openlit-key",
            base_url=f"http://127.0.0.1:{server.server_port}/v1",
            model=DEFAULT_MODEL,
            embedding_model="text-embedding-3-small",
            live=False,
        )
    finally:
        try:
            server.shutdown()
        finally:
            try:
                server.server_close()
            finally:
                thread.join(timeout=5)
                if thread.is_alive():
                    raise RuntimeError(
                        "OpenLIT mock server did not stop within 5 seconds."
                    )


def sync_client(config: ProviderConfig) -> OpenAI:
    kwargs: dict[str, Any] = {
        "api_key": config.api_key,
        "max_retries": 0,
        "timeout": 8,
    }
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return OpenAI(**kwargs)


def async_client(config: ProviderConfig) -> AsyncOpenAI:
    kwargs: dict[str, Any] = {
        "api_key": config.api_key,
        "max_retries": 0,
        "timeout": 8,
    }
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return AsyncOpenAI(**kwargs)
