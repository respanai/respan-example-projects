"""Controlled hook/Connect fixtures; Respan export is an explicit opt-in."""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan_instrumentation_cursor_sdk import CursorSDKInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_METADATA
from respan_tracing import RespanTelemetry
from respan_tracing.exporters import RespanSpanExporter
from respan_tracing.exporters.respan import _span_to_otlp_json
from respan_tracing.utils.span_factory import propagate_attributes

EXAMPLE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EXAMPLE_DIR.parents[2]
DEFAULT_MODEL = "composer-fixture"


def make_custom_identifier(example_name):
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    return os.getenv("RESPAN_EXAMPLE_RUN_ID") or "p10-cursor-" + uuid4().hex


def make_event(example_name, run_id, hook_event_name, **payload):
    return {
        "hook_event_name": hook_event_name,
        "conversation_id": "fixture-" + example_name,
        "generation_id": run_id + ":" + example_name,
        "model_id": DEFAULT_MODEL,
        "cursor_version": "hook-protocol-v1-fixture",
        **payload,
    }


def state_path(run_id):
    root = (
        Path(os.getenv("RESPAN_EXAMPLE_STATE_DIR", tempfile.gettempdir()))
        / "respan-cursor-fixtures"
    )
    root.mkdir(exist_ok=True)
    return root / (run_id.replace("/", "_").replace(":", "_") + ".json")


def make_respan(example_name, state_file):
    key = os.environ.pop("RESPAN_API_KEY", None)
    try:
        telemetry = RespanTelemetry(
            app_name="cursor-sdk-fixtures",
            is_auto_instrument=False,
            is_batching_enabled=False,
        )
    finally:
        if key is not None:
            os.environ["RESPAN_API_KEY"] = key
    instrumentor = CursorSDKInstrumentor(state_path=state_file)
    instrumentor.activate()
    telemetry._cursor_fixture_instrumentor = instrumentor
    return telemetry, instrumentor


def example_attributes(example_name, run_id):
    return propagate_attributes(
        custom_identifier=run_id,
        metadata={
            "run_id": run_id,
            "example_run_id": run_id,
            "scenario": example_name,
            "integration": "cursor-sdk",
        },
    )


class Tags(SpanProcessor):
    def __init__(self, example_name, run_id):
        self.tags = {
            "run_id": run_id,
            "example_run_id": run_id,
            "scenario": example_name,
            "integration": "cursor-sdk",
        }

    def on_start(self, span, parent_context=None):
        span.set_attribute(RESPAN_METADATA, json.dumps(self.tags))
        for name, value in self.tags.items():
            span.set_attribute(f"{RESPAN_METADATA}.{name}", value)


@contextmanager
def tracing(example_name, *, run_id=None, state_file=None):
    run_id = run_id or make_custom_identifier(example_name)
    state_file = state_file or state_path(run_id + "-" + example_name)
    state_file.unlink(missing_ok=True)
    telemetry, instrumentor = make_respan(example_name, state_file)
    from opentelemetry import trace

    provider = trace.get_tracer_provider()
    memory = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(memory))
    provider.add_span_processor(Tags(example_name, run_id))
    if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
        key = os.getenv("RESPAN_API_KEY")
        if not key:
            raise RuntimeError("Explicit export requires RESPAN_API_KEY")
        provider.add_span_processor(
            SimpleSpanProcessor(
                RespanSpanExporter(
                    api_key=key, endpoint="https://api.respan.ai/api/v2/traces"
                )
            )
        )
    try:
        with example_attributes(example_name, run_id):
            yield instrumentor, memory
    finally:
        instrumentor.deactivate()
        telemetry.flush()
        report_dir = os.getenv("RESPAN_EXAMPLE_REPORT_DIR")
        if report_dir:
            path = Path(report_dir)
            path.mkdir(parents=True, exist_ok=True)
            spans = memory.get_finished_spans()
            (path / ("cursor-" + example_name + ".json")).write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "scenario": example_name,
                        "span_count": len(spans),
                        "spans": [_span_to_otlp_json(s) for s in spans],
                    },
                    indent=2,
                )
            )
        print(
            json.dumps(
                {
                    "scenario": example_name,
                    "run_id": run_id,
                    "spans": len(memory.get_finished_spans()),
                }
            )
        )


def replay_events(example_name, events, *, run_id=None):
    with tracing(example_name, run_id=run_id) as (instrumentor, _memory):
        results = [instrumentor.process_event(event) for event in events]
    return results


def print_start(example_name, run_id):
    print(json.dumps({"scenario": example_name, "run_id": run_id}))
