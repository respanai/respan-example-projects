"""Controlled native SDK invocation; trace export requires an explicit opt-in."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan import Respan, propagate_attributes
from respan_instrumentation_vertexai import VertexAIInstrumentor
from respan_tracing.exporters import RespanSpanExporter
from respan_tracing.exporters.respan import _span_to_otlp_json

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]
EXAMPLE_SET = "vertexai"


def run_id():
    return os.getenv("RESPAN_EXAMPLE_RUN_ID", "vertexai-local")


def create_respan(*, capture_content=True):
    export = os.getenv("RESPAN_EXAMPLE_EXPORT") == "1"
    if export:
        load_dotenv(REPO_ROOT / ".env", override=False)
    # The facade reads this environment credential. Suppress its default export
    # so local runs remain local even if the caller already has credentials.
    api_key = os.environ.pop("RESPAN_API_KEY", None)
    try:
        respan = Respan(
            api_key=None,
            app_name="vertexai-examples",
            metadata={
                "example_set": EXAMPLE_SET,
                "example_run_id": run_id(),
                "run_id": run_id(),
            },
            instrumentations=[VertexAIInstrumentor(capture_content=capture_content)],
            is_auto_instrument=False,
            is_batching_enabled=False,
            log_level="WARNING",
        )
    finally:
        if api_key is not None:
            os.environ["RESPAN_API_KEY"] = api_key
    respan.example_memory = InMemorySpanExporter()
    respan.telemetry.add_processor(respan.example_memory, is_batching_enabled=False)
    if export:
        if not api_key:
            raise RuntimeError("RESPAN_EXAMPLE_EXPORT=1 requires RESPAN_API_KEY")
        respan.telemetry.add_processor(
            RespanSpanExporter(
                endpoint="https://api.respan.ai/api/v2/traces", api_key=api_key
            ),
            is_batching_enabled=False,
        )
    return respan


@contextmanager
def example_context(case):
    with propagate_attributes(
        custom_identifier=f"{EXAMPLE_SET}-{case}-{run_id()}",
        trace_group_identifier=f"vertexai_{case}",
        metadata={
            "example_set": EXAMPLE_SET,
            "example_case": case,
            "example_run_id": run_id(),
            "run_id": run_id(),
        },
    ):
        yield


def finish_respan(respan):
    try:
        respan.flush()
        directory = os.getenv("RESPAN_EXAMPLE_REPORT_DIR")
        if directory:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            import sys

            (path / (Path(sys.argv[0]).stem + ".json")).write_text(
                json.dumps(
                    [
                        _span_to_otlp_json(span)
                        for span in respan.example_memory.get_finished_spans()
                    ],
                    indent=2,
                )
            )
    finally:
        respan.shutdown()
        respan.telemetry.tracer.tracer_provider.shutdown()
