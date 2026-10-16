"""Controlled native Pipecat by default; export and paid provider calls are explicit."""

import json
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan import Respan, propagate_attributes
from respan_instrumentation_pipecat import PipecatInstrumentor

ROOT = Path(__file__).resolve().parents[3]


def marker():
    return os.getenv("RESPAN_EXAMPLE_RUN_ID") or "pipecat-" + uuid4().hex[:10]


def create_respan(name, run_id, *, capture=True):
    exporting = os.getenv("RESPAN_PIPECAT_EXPORT") == "1"
    if exporting:
        load_dotenv(ROOT / ".env", override=False)
        if not os.getenv("RESPAN_API_KEY"):
            raise RuntimeError("RESPAN_API_KEY required for explicit export")
    old = os.environ.pop("RESPAN_API_KEY", None) if not exporting else None
    try:
        sdk = Respan(
            api_key=os.getenv("RESPAN_API_KEY") if exporting else None,
            base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
            app_name=name,
            instrumentations=[PipecatInstrumentor(capture_content=capture)],
            metadata={
                "example_set": "pipecat",
                "run_id": run_id,
                "example_run_id": run_id,
            },
            log_level="WARNING",
        )
    finally:
        if old is not None:
            os.environ["RESPAN_API_KEY"] = old
    if not exporting:
        sdk.telemetry.add_processor(exporter=InMemorySpanExporter())
    return sdk


def attributes(name, run_id):
    return propagate_attributes(
        metadata={
            "example_set": "pipecat",
            "example": name,
            "run_id": run_id,
            "example_run_id": run_id,
        },
        trace_group_identifier="pipecat-" + name + "-" + run_id,
    )


def finish_respan(sdk):
    try:
        sdk.flush()
    finally:
        sdk.shutdown()


def print_result(name, result, run_id):
    print("RESPAN_EXAMPLE_RUN_ID=" + run_id)
    print(name + ": " + json.dumps(result, allow_nan=False))
