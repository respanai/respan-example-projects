"""Local released SDK/provider examples with explicit trace export opt-in."""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from opentelemetry.sdk.trace import SpanLimits, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan_instrumentation_replicate import ReplicateInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA


class Markers(SpanProcessor):
    def __init__(self, metadata):
        self.metadata = metadata

    def on_start(self, span, parent_context=None):
        span.set_attribute(RESPAN_METADATA, json.dumps(self.metadata))
        for k, v in self.metadata.items():
            span.set_attribute(RESPAN_METADATA + "." + k, v)

    def on_end(self, span):
        pass


class Runtime:
    def __init__(self, name, capture=True):
        self.name = name
        self.run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID") or "replicate-" + uuid4().hex
        self.provider = TracerProvider(span_limits=SpanLimits(max_attributes=4096))
        self.memory = InMemorySpanExporter()
        self.wire = []
        self.provider.add_span_processor(
            Markers(
                {
                    "integration": "replicate",
                    "scenario": name,
                    "run_id": self.run_id,
                    "example_run_id": self.run_id,
                }
            )
        )
        self.provider.add_span_processor(SimpleSpanProcessor(self.memory))
        if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
            from dotenv import load_dotenv
            from respan_tracing.exporters import RespanSpanExporter

            load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)
            key = os.getenv("RESPAN_API_KEY") or os.getenv("RESPAN_GATEWAY_API_KEY")
            if not key:
                raise RuntimeError("RESPAN_API_KEY required for explicit trace export")
            exporter = RespanSpanExporter(
                endpoint=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
                api_key=key,
            )
            original = exporter._session.post

            def post(url, *args, **kwargs):
                payload = (
                    json.loads(kwargs["data"])
                    if kwargs.get("data")
                    else kwargs.get("json")
                )
                response = original(url, *args, **kwargs)
                if os.getenv("RESPAN_EXAMPLE_WIRE_DIR"):
                    self.wire.append(
                        {"payload": payload, "http_status": response.status_code}
                    )
                return response

            exporter._session.post = post
            self.provider.add_span_processor(SimpleSpanProcessor(exporter))
        self.owner = ReplicateInstrumentor(
            tracer_provider=self.provider, capture_content=capture
        )
        self.owner.activate()

    def workflow(self):
        return self.provider.get_tracer("application").start_as_current_span(
            "replicate.example", attributes={RESPAN_LOG_TYPE: "workflow"}
        )

    def close(self):
        self.owner.deactivate()
        self.provider.force_flush()
        spans = self.memory.get_finished_spans()
        ids = {s.context.span_id for s in spans}
        assert all(s.parent is None or s.parent.span_id in ids for s in spans)
        report = {
            "run_id": self.run_id,
            "scenario": self.name,
            "spans": [
                {
                    "name": s.name,
                    "trace_id": format(s.context.trace_id, "032x"),
                    "span_id": format(s.context.span_id, "016x"),
                    "parent_span_id": format(s.parent.span_id, "016x")
                    if s.parent
                    else None,
                    "attributes": dict(s.attributes),
                    "status": s.status.status_code.name,
                    "status_description": s.status.description,
                    "events": [
                        {"name": e.name, "attributes": dict(e.attributes)}
                        for e in s.events
                    ],
                }
                for s in spans
            ],
        }
        for variable, data in [
            ("RESPAN_EXAMPLE_REPORT_DIR", report),
            (
                "RESPAN_EXAMPLE_WIRE_DIR",
                {"run_id": self.run_id, "scenario": self.name, "entries": self.wire},
            ),
        ]:
            directory = os.getenv(variable)
            if directory:
                path = Path(directory)
                path.mkdir(parents=True, exist_ok=True)
                (path / (self.name + ".json")).write_text(json.dumps(data, indent=2))
        print(f"scenario={self.name} run_id={self.run_id} local_spans={len(spans)}")
        self.provider.shutdown()
