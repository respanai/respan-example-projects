"""Local-first official Ollama clients using HTTPX's native mock transport."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from pathlib import Path

import httpx
import ollama
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv_ai import SpanAttributes
from respan_instrumentation_ollama import OllamaInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA
from respan_tracing.utils.span_factory import propagate_attributes

EXAMPLE_DIR = Path(__file__).resolve().parent
MODEL = "llama3.2"
CHAT = {
    "model": MODEL,
    "message": {
        "role": "assistant",
        "content": "Native Ollama tracing works.",
        "thinking": "Controlled reasoning.",
    },
    "done": True,
    "prompt_eval_count": 0,
    "eval_count": 0,
    "prompt_eval_cached_count": 0,
}


class Body(httpx.SyncByteStream):
    def __init__(self, frames):
        self.frames = frames
        self.reads = 0
        self.closed = False

    def __iter__(self):
        for frame in self.frames:
            self.reads += 1
            yield json.dumps(frame).encode() + b"\n" if type(frame) is dict else frame

    def close(self):
        self.closed = True


class AsyncBody(httpx.AsyncByteStream):
    def __init__(self, frames):
        self.body = Body(frames)

    async def __aiter__(self):
        for data in self.body:
            yield data

    async def aclose(self):
        self.body.close()


def client(payload=CHAT, *, frames=None, status=200, asynchronous=False):
    body = (
        (AsyncBody(frames) if asynchronous else Body(frames))
        if frames is not None
        else None
    )
    requests = []

    def response(request):
        requests.append(request)
        return (
            httpx.Response(status, stream=body)
            if body is not None
            else httpx.Response(status, json=payload)
        )

    async def async_response(request):
        await asyncio.sleep(0)
        return response(request)

    cls = ollama.AsyncClient if asynchronous else ollama.Client
    c = cls(transport=httpx.MockTransport(async_response if asynchronous else response))
    return c, body, requests


def runtime(case):
    provider = TracerProvider()
    local = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(local))
    if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
        from dotenv import load_dotenv
        from respan_tracing.exporters.respan import RespanSpanExporter

        load_dotenv(
            Path(
                os.getenv(
                    "RESPAN_EXAMPLE_ENV_FILE", str(EXAMPLE_DIR.parents[2] / ".env")
                )
            ),
            override=False,
        )
        if not os.getenv("RESPAN_API_KEY"):
            raise RuntimeError("RESPAN_API_KEY is required for explicit export")
        exporter = RespanSpanExporter(
            api_key=os.environ["RESPAN_API_KEY"],
            endpoint=os.getenv(
                "RESPAN_TRACE_ENDPOINT", "https://api.respan.ai/api/v2/traces"
            ),
        )
        wire_path = os.getenv("RESPAN_EXAMPLE_WIRE_PATH")
        if wire_path:
            actual_post = exporter._session.post

            def observe(url, *args, **kwargs):
                payload = kwargs.get("json")
                if payload is None and kwargs.get("data") is not None:
                    payload = json.loads(kwargs["data"])
                response = actual_post(url, *args, **kwargs)
                with open(wire_path, "a", encoding="utf-8") as file:
                    file.write(
                        json.dumps(
                            {"payload": payload, "http_status": response.status_code}
                        )
                        + "\n"
                    )
                return response

            exporter._session.post = observe
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    instrumentor = OllamaInstrumentor(tracer_provider=provider)
    instrumentor.activate()
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID", "ollama-local-" + uuid.uuid4().hex)
    metadata = {"run_id": marker, "example_set": "ollama", "example_case": case}
    attrs = {
        RESPAN_METADATA: json.dumps(metadata),
        RESPAN_LOG_TYPE: "workflow",
        SpanAttributes.TRACELOOP_SPAN_KIND: "workflow",
        SpanAttributes.TRACELOOP_ENTITY_NAME: case,
        SpanAttributes.TRACELOOP_ENTITY_PATH: "",
    }
    return provider, local, instrumentor, marker, metadata, attrs


def run_case(case, action):
    provider, local, instrumentor, marker, metadata, attributes = runtime(case)
    try:
        with (
            propagate_attributes(metadata=metadata),
            provider.get_tracer("ollama.examples").start_as_current_span(
                case, attributes=attributes
            ),
        ):
            result = action(provider)
        provider.force_flush()
        spans = local.get_finished_spans()
        path = os.getenv("RESPAN_EXAMPLE_LOCAL_PATH")
        if path:
            with open(path, "a", encoding="utf-8") as file:
                file.writelines(
                    json.dumps(
                        {
                            "case": case,
                            "run_id": marker,
                            "name": span.name,
                            "trace_id": f"{span.context.trace_id:032x}",
                            "span_id": f"{span.context.span_id:016x}",
                            "parent_id": f"{span.parent.span_id:016x}"
                            if span.parent
                            else None,
                            "status": span.status.status_code.name,
                            "attributes": dict(span.attributes),
                        }
                    )
                    + "\n"
                    for span in spans
                )
        print(f"{case}: {result}; spans={len(spans)}; run_id={marker}")
    finally:
        instrumentor.deactivate()
        provider.shutdown()
