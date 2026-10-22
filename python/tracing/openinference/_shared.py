"""Fixture-default generic OI pipeline with explicit optional Respan export."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan_instrumentation_openinference import OpenInferenceInstrumentor
from respan_tracing import RespanTelemetry
from respan_tracing import workflow as native_workflow
from respan_tracing.exporters import RespanSpanExporter, propagate_attributes

workflow = native_workflow

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
INTEGRATION = "openinference"


class ContractSourceProcessor(SpanProcessor):
    """Real processor delegate for controlled OI semantic-contract fixtures."""

    def on_start(self, span: Any, parent_context: Any = None) -> None:
        pass

    def on_end(self, span: Any) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True


def load_root_env() -> None:
    load_dotenv(
        Path(os.getenv("RESPAN_EXAMPLE_ENV_FILE", PROJECT_ROOT / ".env")),
        override=False,
    )


def require_respan_api_key() -> str:
    load_root_env()
    key = os.getenv("RESPAN_API_KEY")
    if not key:
        raise RuntimeError("Export requires RESPAN_API_KEY in the configured .env")
    return key


def example_run_id() -> str:
    return (
        os.getenv("RESPAN_EXAMPLE_RUN_ID")
        or f"openinference-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )


class Tracing:
    def __init__(self, example_name: str, run_id: str):
        self.example_name, self.run_id = example_name, run_id
        export = os.getenv("RESPAN_EXAMPLE_EXPORT") == "1"
        key = require_respan_api_key() if export else None
        previous = os.environ.pop("RESPAN_API_KEY", None)
        try:
            self.telemetry = RespanTelemetry(
                app_name="openinference-contract-examples",
                api_key=None,
                base_url=os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL).rstrip(
                    "/"
                ),
                is_auto_instrument=False,
                is_batching_enabled=False,
                log_level="WARNING",
            )
        finally:
            if previous is not None:
                os.environ["RESPAN_API_KEY"] = previous
        self.memory = InMemorySpanExporter()
        self.telemetry.add_processor(self.memory, is_batching_enabled=False)
        self.instrumentor = OpenInferenceInstrumentor(ContractSourceProcessor)
        self.instrumentor.activate()
        self.delegates = []
        self.acknowledgments = []
        self.otlp_payloads = []
        if export:
            exporter = RespanSpanExporter(
                endpoint=os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL).rstrip(
                    "/"
                )
                + "/v2/traces",
                api_key=key,
            )
            self.telemetry.add_processor(exporter, is_batching_enabled=False)
            original = exporter._session.post

            def post(*args, **kwargs):
                response = original(*args, **kwargs)
                self.otlp_payloads.append(json.loads(kwargs["data"]))
                self.acknowledgments.append(response.status_code)
                return response

            exporter._session.post = post

    def delegate(self, delegate_class, **kwargs):
        wrapper = OpenInferenceInstrumentor(delegate_class, **kwargs)
        wrapper.activate()
        self.delegates.append(wrapper)
        return wrapper

    def flush(self):
        self.telemetry.flush()

    def shutdown(self):
        self.flush()
        spans = self.memory.get_finished_spans()
        wire_dir = os.getenv("RESPAN_EXAMPLE_WIRE_DIR")
        if wire_dir:
            directory = Path(wire_dir)
            directory.mkdir(parents=True, exist_ok=True)
            records = [
                {
                    "span_id": format(s.context.span_id, "016x"),
                    "trace_id": format(s.context.trace_id, "032x"),
                    "parent_id": format(s.parent.span_id, "016x") if s.parent else None,
                    "name": s.name,
                    "attributes": dict(s.attributes),
                    "status": s.status.status_code.name,
                    "description": s.status.description,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "events": [
                        {"name": e.name, "attributes": dict(e.attributes or {})}
                        for e in s.events
                    ],
                }
                for s in spans
            ]
            (directory / f"{self.example_name}.json").write_text(
                json.dumps(
                    {
                        "marker": self.run_id,
                        "spans": records,
                        "http_statuses": self.acknowledgments,
                        "otlp_payloads": self.otlp_payloads,
                    },
                    indent=2,
                )
                + "\n"
            )
        for delegate in reversed(self.delegates):
            delegate.deactivate()
        self.instrumentor.deactivate()
        self.telemetry.tracer.tracer_provider.shutdown()
        if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
            assert self.acknowledgments and all(
                status == 200 for status in self.acknowledgments
            ), self.acknowledgments
        print(f"spans={len(spans)} http_200={self.acknowledgments.count(200)}")


def make_respan(example_name: str, run_id: str) -> Tracing:
    return Tracing(example_name, run_id)


def workflow_name(example_name: str) -> str:
    return f"openinference_{example_name.replace('-', '_')}"


@contextmanager
def example_attributes(example_name: str, run_id: str) -> Iterator[None]:
    with propagate_attributes(
        custom_identifier=f"{INTEGRATION}-{example_name}-{run_id}",
        trace_group_identifier=workflow_name(example_name),
        metadata={
            "run_id": run_id,
            "example_run_id": run_id,
            "integration": INTEGRATION,
            "example": example_name,
            "workflow_name": workflow_name(example_name),
        },
    ):
        yield


def tracer():
    return trace.get_tracer("openinference.contract.examples")


def finish_respan(respan: Tracing) -> None:
    respan.shutdown()


def print_result(example_name: str, run_id: str, result: str) -> None:
    print(
        f"example={example_name} example_run_id={run_id} workflow_name={workflow_name(example_name)}"
    )
    print(result)
