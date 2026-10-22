"""Local released-SDK fixtures by default; explicit opt-in for Respan export."""

from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan_instrumentation_agentops import AgentOpsInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_METADATA

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPORT = os.getenv("RESPAN_EXPORT", "0") == "1"
if EXPORT:
    load_dotenv(
        Path(os.getenv("RESPAN_ENV_FILE", str(REPO_ROOT / ".env"))), override=False
    )
RUN_ID = os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"agentops-{uuid.uuid4().hex[:12]}"


class Marker(SpanProcessor):
    def __init__(self, example, workflow):
        self.metadata = {
            "run_id": RUN_ID,
            "example_run_id": RUN_ID,
            "framework": "agentops",
            "example": example,
            "workflow_name": workflow,
        }

    def on_start(self, span, parent_context=None):
        span.set_attribute(RESPAN_METADATA, json.dumps(self.metadata))
        for key, value in self.metadata.items():
            span.set_attribute(f"{RESPAN_METADATA}.{key}", value)

    def on_end(self, span):
        pass

    def shutdown(self):
        pass

    def force_flush(self, timeout_millis=30000):
        return True


class Telemetry:
    def __init__(self, provider, owner, exporter):
        self.provider = provider
        self.owner = owner
        self.exporter = exporter

    def shutdown(self):
        self.provider.force_flush()
        self.owner.deactivate()
        spans = self.exporter.get_finished_spans()
        print(f"LOCAL_TRACE_COUNT={len(spans)}")
        directory = os.getenv("AGENTOPS_CAPTURE_DIR")
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


def build_respan(*, example_name, workflow_name):
    if EXPORT:
        from respan_tracing import RespanTelemetry

        RespanTelemetry(
            app_name=f"agentops-{example_name}",
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
    provider.add_span_processor(Marker(example_name, workflow_name))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    owner = AgentOpsInstrumentor()
    owner.activate()
    return Telemetry(provider, owner, exporter)


@contextmanager
def example_scope(example_name):
    yield
