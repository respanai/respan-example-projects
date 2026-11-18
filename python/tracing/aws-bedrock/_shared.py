"""Native botocore fixtures and local-first OpenTelemetry example lifecycle."""

from __future__ import annotations

import base64
import io
import json
import os
import struct
import uuid
import zlib
from pathlib import Path

import boto3
from botocore.awsrequest import AWSResponse
from botocore.config import Config
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv_ai import SpanAttributes
from respan_instrumentation_aws_bedrock import AWSBedrockInstrumentor
from respan_sdk.constants.llm_logging import LOG_TYPE_WORKFLOW
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA
from urllib3.response import HTTPResponse

EXAMPLE_DIR = Path(__file__).resolve().parent


def create_bedrock_client(*, live=False):
    if live:
        return boto3.client(
            "bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1")
        )
    return boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id="controlled",
        aws_secret_access_key="controlled",
        endpoint_url="https://bedrock-runtime.invalid",
        config=Config(retries={"max_attempts": 0}),
    )


def get_model_id():
    return os.getenv("AWS_BEDROCK_MODEL_ID", "anthropic.controlled")


def frame(kind, payload, *, message_type="event"):
    headers = b""
    for key, data in (
        (":message-type", message_type),
        (":event-type", kind),
        (":content-type", "application/json"),
    ):
        key, data = key.encode(), data.encode()
        headers += (
            bytes([len(key)]) + key + b"\x07" + struct.pack(">H", len(data)) + data
        )
    encoded = json.dumps(payload).encode()
    prelude = struct.pack(">II", 16 + len(headers) + len(encoded), len(headers))
    encoded = prelude + struct.pack(">I", zlib.crc32(prelude)) + headers + encoded
    return encoded + struct.pack(">I", zlib.crc32(encoded))


def transport(client, payload, *, status=200, event_stream=False):
    raw = payload if type(payload) is bytes else json.dumps(payload).encode()
    headers = {
        "content-type": "application/vnd.amazon.eventstream"
        if event_stream
        else "application/json",
        "content-length": str(len(raw)),
    }
    response = AWSResponse(
        "https://bedrock-runtime.invalid",
        status,
        headers,
        HTTPResponse(body=io.BytesIO(raw), preload_content=False),
    )
    client._endpoint.http_session.send = lambda request: response
    return response


def event_frames(events, *, invoke=False):
    if invoke:
        return b"".join(
            frame(
                "chunk",
                {"bytes": base64.b64encode(json.dumps(event).encode()).decode()},
            )
            for event in events
        )
    return b"".join(frame(kind, payload) for kind, payload in events)


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
            endpoint="https://api.respan.ai/api/v2/traces",
        )
        wire_path = os.getenv("RESPAN_EXAMPLE_WIRE_PATH")
        if wire_path:
            actual_post = exporter._session.post

            def observe(url, *args, **kwargs):
                body = kwargs.get("json")
                if body is None and kwargs.get("data") is not None:
                    body = json.loads(kwargs["data"])
                # These are the exporter's actual HTTP bodies, never rebuilt OTLP.
                with open(wire_path, "a", encoding="utf-8") as file:
                    file.write(json.dumps(body) + "\n")
                response = actual_post(url, *args, **kwargs)
                status_path = os.getenv("RESPAN_EXAMPLE_HTTP_PATH")
                if status_path:
                    with open(status_path, "a", encoding="utf-8") as file:
                        file.write(
                            json.dumps({"status_code": response.status_code}) + "\n"
                        )
                return response

            exporter._session.post = observe
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    instrumentor = AWSBedrockInstrumentor(tracer_provider=provider)
    instrumentor.activate()
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID", "bedrock-local-" + uuid.uuid4().hex)
    attrs = {
        RESPAN_METADATA: json.dumps(
            {"run_id": marker, "example_set": "aws-bedrock", "example_case": case}
        ),
        RESPAN_LOG_TYPE: LOG_TYPE_WORKFLOW,
        SpanAttributes.TRACELOOP_SPAN_KIND: "workflow",
        SpanAttributes.TRACELOOP_ENTITY_NAME: case,
        SpanAttributes.TRACELOOP_ENTITY_PATH: "",
    }
    return provider, local, instrumentor, marker, attrs


def run_case(case, action):
    provider, local, instrumentor, marker, attrs = runtime(case)
    try:
        with provider.get_tracer("bedrock.examples").start_as_current_span(
            case, attributes=attrs
        ):
            result = action(provider)
        provider.force_flush()
        spans = local.get_finished_spans()
        output_path = os.getenv("RESPAN_EXAMPLE_LOCAL_PATH")
        if output_path:
            with open(output_path, "a", encoding="utf-8") as file:
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
    return marker
