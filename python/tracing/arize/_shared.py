"""Credential-free native Arize fixtures with optional controlled Respan export."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from _fixture import FixtureTransport
from dotenv import load_dotenv
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan import Respan
from respan_instrumentation_arize import ArizeInstrumentor


def load_repo_env():
    for parent in Path(__file__).resolve().parents:
        file = parent / ".env"
        if file.exists():
            load_dotenv(file, override=False)


def new_run_id():
    return os.getenv("RESPAN_EXAMPLE_RUN_ID") or uuid4().hex[:12]


@contextmanager
def example(name, *, failure=False, capture_content=True):
    marker = new_run_id()
    exporting = os.getenv("RESPAN_ARIZE_EXPORT") == "1"
    if exporting:
        load_repo_env()
    previous = os.environ.pop("RESPAN_API_KEY", None) if not exporting else None
    try:
        respan = Respan(
            app_name="arize-controlled-example",
            api_key=os.getenv("RESPAN_API_KEY") if exporting else None,
            base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
            instrumentations=[ArizeInstrumentor(capture_content=capture_content)],
            metadata={"run_id": marker, "example_set": "arize", "example_name": name},
        )
    finally:
        if previous is not None:
            os.environ["RESPAN_API_KEY"] = previous
    if not exporting:
        respan.telemetry.add_processor(exporter=InMemorySpanExporter())
    fixture = FixtureTransport(fail=failure)
    try:
        with (
            respan.propagate_attributes(
                metadata={
                    "run_id": marker,
                    "example_set": "arize",
                    "example_name": name,
                },
                trace_group_identifier=name + "-" + marker,
            ),
            respan.telemetry.get_client().start_span(name, kind="workflow"),
        ):
            yield fixture.client
    finally:
        fixture.close()
        try:
            respan.flush()
        finally:
            respan.shutdown()
    print("RESPAN_EXAMPLE_RUN_ID=" + marker)


def print_result(name, result):
    # Avoid rendering SDK objects, which can contain account/credential fields.
    shape = getattr(result, "shape", None)
    print(
        name + ": " + type(result).__name__ + (str(shape) if shape is not None else "")
    )
