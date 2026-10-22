"""Local Temporal fixtures, with explicit remote-server and Respan-export modes."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan_instrumentation_temporal import TemporalInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_METADATA
from respan_tracing.exporters import RespanSpanExporter
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]


def marker() -> str:
    return os.getenv("RESPAN_EXAMPLE_RUN_ID", "temporal-local")


def temporal_id(case: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "-", f"{marker()}-{case}")[:200]


class FixtureMarker(SpanProcessor):
    """Attach only deliberate synthetic run labels, independently of payloads."""

    def __init__(self, case: str):
        self.case = case

    def on_start(self, span, parent_context=None):
        labels = {
            "run_id": marker(),
            "example_run_id": marker(),
            "example_set": "temporal",
            "case": self.case,
        }
        span.set_attribute(RESPAN_METADATA, json.dumps(labels))
        for name, value in labels.items():
            span.set_attribute(f"{RESPAN_METADATA}.{name}", value)

    def on_end(self, span):
        pass

    def shutdown(self):
        pass

    def force_flush(self, timeout_millis=30000):
        return True


class FixtureTelemetry:
    def __init__(
        self,
        case: str,
        provider: TracerProvider,
        exporter: InMemorySpanExporter,
        instrumentor: TemporalInstrumentor,
    ) -> None:
        self.case = case
        self.provider = provider
        self.exporter = exporter
        self.instrumentor = instrumentor

    def flush(self) -> None:
        assert self.provider.force_flush()

    def shutdown(self) -> None:
        spans = self.exporter.get_finished_spans()
        report = {
            "run_id": marker(),
            "case": self.case,
            "span_count": len(spans),
            "spans": [json.loads(span.to_json()) for span in spans],
        }
        destination = os.getenv("RESPAN_EXAMPLE_REPORT_DIR")
        if destination:
            directory = Path(destination)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{self.case}.json").write_text(json.dumps(report, indent=2))
        print({"case": self.case, "span_count": len(spans), "run_id": marker()})
        self.instrumentor.deactivate()
        self.provider.shutdown()


def create_respan(
    case: str, *, capture_content: bool = True
) -> tuple[FixtureTelemetry, TemporalInstrumentor]:
    """Use an application-owned OTel provider; local mode sends no HTTP requests."""
    provider = TracerProvider()
    provider.add_span_processor(FixtureMarker(case))
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
        load_dotenv(REPO_ROOT / ".env", override=False)
        provider.add_span_processor(
            BatchSpanProcessor(
                RespanSpanExporter(
                    api_key=os.environ["RESPAN_API_KEY"],
                    endpoint="https://api.respan.ai/api",
                )
            )
        )
    trace.set_tracer_provider(provider)
    instrumentor = TemporalInstrumentor(
        capture_content=capture_content, always_create_workflow_spans=True
    )
    instrumentor.activate()
    return FixtureTelemetry(case, provider, exporter, instrumentor), instrumentor


async def create_environment(instrumentor: TemporalInstrumentor) -> WorkflowEnvironment:
    if os.getenv("TEMPORAL_EXAMPLE_REMOTE") == "1":
        address = os.environ["TEMPORAL_ADDRESS"]
        client = await Client.connect(
            address, namespace=os.getenv("TEMPORAL_NAMESPACE", "default")
        )
        return WorkflowEnvironment.from_client(client)
    return await WorkflowEnvironment.start_time_skipping(
        interceptors=[instrumentor.interceptor],
        test_server_existing_path=os.getenv("TEMPORAL_TEST_SERVER_PATH"),
    )


def finish_respan(respan: FixtureTelemetry) -> None:
    try:
        respan.flush()
    finally:
        respan.shutdown()
