"""Native local Marqo examples with explicit controlled trace export."""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv_ai import SpanAttributes
from respan_instrumentation_marqo import MarqoInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA
from respan_tracing.utils.span_factory import propagate_attributes

EXAMPLE_DIR = Path(__file__).resolve().parent
if "--export" in sys.argv:
    os.environ["RESPAN_EXAMPLE_EXPORT"] = "1"


class Marker(SpanProcessor):
    def __init__(self, metadata):
        self.metadata = metadata

    def on_start(self, span, parent_context=None):
        span.set_attribute(RESPAN_METADATA, json.dumps(self.metadata))
        for key, item in self.metadata.items():
            span.set_attribute(f"{RESPAN_METADATA}.{key}", item)

    def on_end(self, span):
        pass

    def shutdown(self):
        pass


def runtime(case):
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID", "marqo-local-" + uuid.uuid4().hex)
    metadata = {"run_id": marker, "example_set": "marqo", "example_case": case}
    provider = TracerProvider()
    local = InMemorySpanExporter()
    provider.add_span_processor(Marker(metadata))
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
    instrumentor = MarqoInstrumentor(tracer_provider=provider)
    instrumentor.activate()
    attrs = {
        RESPAN_METADATA: json.dumps(metadata),
        RESPAN_LOG_TYPE: "workflow",
        SpanAttributes.TRACELOOP_ENTITY_NAME: case,
        SpanAttributes.TRACELOOP_ENTITY_PATH: "",
    }
    return provider, local, instrumentor, marker, metadata, attrs


def run_case(case, action):
    provider, local, instrumentor, marker, metadata, attributes = runtime(case)
    try:
        with (
            propagate_attributes(metadata=metadata),
            provider.get_tracer("marqo.examples").start_as_current_span(
                case, attributes=attributes
            ),
        ):
            result = action(provider, local)
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
                            "status_description": span.status.description,
                            "events": [
                                {
                                    "name": event.name,
                                    "attributes": dict(event.attributes or {}),
                                }
                                for event in span.events
                            ],
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


from contextlib import contextmanager


@contextmanager
def marqo_client():
    import marqo
    from _loopback import server

    with server() as (url, requests):
        yield marqo.Client(url=url), requests
