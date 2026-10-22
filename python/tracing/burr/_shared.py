"""Local Burr example runtime, with explicit opt-in for Respan export."""

from __future__ import annotations

import json
import os
import uuid
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan_instrumentation_burr import BurrInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_METADATA

EXAMPLE_DIR = Path(__file__).resolve().parent
ROOT_ENV = EXAMPLE_DIR.parents[2] / ".env"


def load_repo_env() -> None:
    if not ROOT_ENV.exists():
        return
    for raw in ROOT_ENV.read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def new_run_id(example_name: str) -> str:
    return (
        os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"{example_name}-{uuid.uuid4().hex[:10]}"
    )


class _Markers(SpanProcessor):
    def __init__(self, metadata: dict[str, str]) -> None:
        self.metadata = metadata

    def on_start(self, span: Any, parent_context: Any = None) -> None:
        span.set_attribute(RESPAN_METADATA, json.dumps(self.metadata))

    def on_end(self, span: Any) -> None:
        pass


class ExampleRuntime:
    def __init__(
        self,
        *,
        workflow_name: str,
        run_id: str,
        example_name: str,
        capture_content: bool,
    ) -> None:
        self.run_id, self.example_name = run_id, example_name
        self.provider = TracerProvider()
        self.memory = InMemorySpanExporter()
        self.provider.add_span_processor(
            _Markers(
                {
                    "example_set": "burr",
                    "example_name": example_name,
                    "workflow_name": workflow_name,
                    "run_id": run_id,
                }
            )
        )
        self.provider.add_span_processor(SimpleSpanProcessor(self.memory))
        if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
            load_repo_env()
            key = os.getenv("RESPAN_API_KEY") or os.getenv("RESPAN_GATEWAY_API_KEY")
            if not key:
                raise RuntimeError(
                    "RESPAN_API_KEY is required for explicit trace export"
                )
            from respan_tracing.exporters import RespanSpanExporter

            self.provider.add_span_processor(
                SimpleSpanProcessor(
                    RespanSpanExporter(
                        endpoint=os.getenv(
                            "RESPAN_BASE_URL", "https://api.respan.ai/api"
                        ),
                        api_key=key,
                    )
                )
            )
        trace.set_tracer_provider(self.provider)
        self.owner = BurrInstrumentor(capture_content=capture_content)
        self.owner.activate()

    def shutdown(self) -> None:
        try:
            self.provider.force_flush()
            spans = self.memory.get_finished_spans()
            assert spans, "The native Burr example did not emit lifecycle spans"
            parent_ids = {span.context.span_id for span in spans}
            assert all(
                span.parent is None or span.parent.span_id in parent_ids
                for span in spans
            )
            report = {
                "run_id": self.run_id,
                "scenario": self.example_name,
                "span_count": len(spans),
                "spans": [
                    {
                        "name": span.name,
                        "trace_id": format(span.context.trace_id, "032x"),
                        "span_id": format(span.context.span_id, "016x"),
                        "parent_span_id": format(span.parent.span_id, "016x")
                        if span.parent
                        else None,
                        "attributes": dict(span.attributes),
                        "status": span.status.status_code.name,
                        "status_description": span.status.description,
                        "events": [
                            {"name": event.name, "attributes": dict(event.attributes)}
                            for event in span.events
                        ],
                    }
                    for span in spans
                ],
            }
            report_dir = os.getenv("RESPAN_EXAMPLE_REPORT_DIR")
            if report_dir:
                path = Path(report_dir)
                path.mkdir(parents=True, exist_ok=True)
                (path / f"{self.example_name}.json").write_text(
                    json.dumps(report, indent=2)
                )
            print(f"local_spans={len(spans)}")
        finally:
            self.owner.deactivate()
            self.provider.shutdown()


def create_respan(
    *, workflow_name: str, run_id: str, example_name: str, capture_content: bool = True
) -> ExampleRuntime:
    return ExampleRuntime(
        workflow_name=workflow_name,
        run_id=run_id,
        example_name=example_name,
        capture_content=capture_content,
    )


def workflow_context(respan: ExampleRuntime, **kwargs: Any) -> Any:
    return nullcontext()


def print_trace_lookup(*, workflow_name: str, run_id: str) -> None:
    print(f"workflow_name={workflow_name}")
    print(f"RESPAN_EXAMPLE_RUN_ID={run_id}")
