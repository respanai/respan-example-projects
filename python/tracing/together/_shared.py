"""Controlled native SDK invocation; trace export requires an explicit opt-in."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan import Respan, propagate_attributes
from respan_instrumentation_together import TogetherInstrumentor
from respan_tracing.exporters import RespanSpanExporter
from respan_tracing.exporters.respan import _span_to_otlp_json

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]
EXAMPLE_SET = "together"


def run_id():
    return os.getenv("RESPAN_EXAMPLE_RUN_ID", "together-local")


def create_respan(*, capture_content=True, marker=None):
    export = os.getenv("RESPAN_EXAMPLE_EXPORT") == "1"
    if export:
        load_dotenv(REPO_ROOT / ".env", override=False)
    # The facade reads this environment credential. Suppress its default export
    # so local runs remain local even if the caller already has credentials.
    api_key = os.environ.pop("RESPAN_API_KEY", None)
    try:
        respan = Respan(
            api_key=None,
            app_name="together-examples",
            metadata={
                "example_set": EXAMPLE_SET,
                "example_run_id": marker or run_id(),
                "run_id": marker or run_id(),
            },
            instrumentations=[TogetherInstrumentor(capture_content=capture_content)],
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
        trace_group_identifier=f"together_{case}",
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


from uuid import uuid4

import httpx
from _fixtures import NativeRuntime
from together import AsyncTogether, Together


def load_root_env():
    load_dotenv(REPO_ROOT / ".env", override=False)


def model_name():
    return os.getenv("RESPAN_TOGETHER_MODEL", "native-model")


def completion_model_name():
    return os.getenv("RESPAN_TOGETHER_COMPLETION_MODEL", model_name())


def embedding_model_name():
    return os.getenv("RESPAN_TOGETHER_EMBEDDING_MODEL", "native-embedding")


def rerank_model_name():
    return os.getenv("RESPAN_TOGETHER_RERANK_MODEL", "native-rerank")


def image_model_name():
    return os.getenv("RESPAN_TOGETHER_IMAGE_MODEL", "native-image")


def make_custom_identifier(case):
    return (
        os.getenv("RESPAN_EXAMPLE_RUN_ID")
        or "together-" + case + "-" + uuid4().hex[:12]
    )


def workflow_name(case):
    return "together_" + case.replace("-", "_")


def make_respan(case, marker):
    return create_respan(marker=marker)


def _runtime(error_status):
    runtime = NativeRuntime()
    if error_status is not None:

        def respond(request):
            return httpx.Response(
                error_status,
                json={"error": {"message": "controlled provider failure"}},
                request=request,
            )

        runtime.respond = respond
    return runtime


def _live():
    if os.getenv("RESPAN_TOGETHER_LIVE") != "1":
        return None
    load_root_env()
    key = os.environ.get("TOGETHER_API_KEY")
    if not key:
        raise RuntimeError("RESPAN_TOGETHER_LIVE=1 requires TOGETHER_API_KEY")
    if not os.environ.get("RESPAN_TOGETHER_MODEL"):
        raise RuntimeError("Set RESPAN_TOGETHER_MODEL for the explicit live call")
    return key


def make_client(*, error_status=None):
    key = _live() if error_status is None else None
    return Together(api_key=key) if key else _runtime(error_status).client()


def make_async_client(*, error_status=None):
    key = _live() if error_status is None else None
    return AsyncTogether(api_key=key) if key else _runtime(error_status).async_client()


@contextmanager
def example_attributes(case, custom_identifier=None):
    marker = custom_identifier or make_custom_identifier(case)
    with propagate_attributes(
        custom_identifier=marker,
        trace_group_identifier=workflow_name(case),
        metadata={
            "example_set": EXAMPLE_SET,
            "example_case": case,
            "example_run_id": marker,
            "run_id": marker,
        },
    ):
        yield marker


def first_message_text(response):
    return (
        response.choices[0].message.content
        if response.choices
        and response.choices[0].message
        and response.choices[0].message.content is not None
        else ""
    )


def first_text_completion(response):
    return response.choices[0].text if response.choices else ""


def print_start(case, marker):
    print(f"example={case} marker={marker}", flush=True)


def print_result(case, marker, result):
    print(json.dumps({"example": case, "marker": marker, "result": result}), flush=True)
