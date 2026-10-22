"""Real IBM clients; local HTTPX JSON/SSE fixtures and explicit Respan export."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from _native import runtime as native

__all__ = ["native"]

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv_ai import SpanAttributes
from respan_instrumentation_watsonx import WatsonxInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA
from respan_tracing.utils.span_factory import propagate_attributes

EXAMPLE_DIR = Path(__file__).resolve().parent
GEN = {
    "model_id": "reported-granite",
    "results": [
        {
            "generated_text": "Native Watsonx tracing works.",
            "input_token_count": 0,
            "generated_token_count": 0,
            "stop_reason": "eos_token",
        }
    ],
    "custom": {"flag": False},
}
CHAT = {
    "model_id": "reported-granite",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "",
                "reasoning_content": "Controlled reasoning.",
                "tool_calls": [
                    {
                        "id": "call-weather",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city":"Tokyo"}',
                        },
                    }
                ],
            },
        }
    ],
    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    "custom": {"flag": False},
}
EMB = {
    "model_id": "reported-slate",
    "results": [{"embedding": [0.0] * 5001, "input": "controlled"}],
    "input_token_count": 0,
    "custom": {"flag": False},
}


def close(client):
    client.httpx_client.close()


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
    instrumentor = WatsonxInstrumentor(tracer_provider=provider)
    instrumentor.activate()
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID", "watsonx-local-" + uuid.uuid4().hex)
    metadata = {"run_id": marker, "example_set": "watsonx", "example_case": case}
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
            provider.get_tracer("watsonx.examples").start_as_current_span(
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
