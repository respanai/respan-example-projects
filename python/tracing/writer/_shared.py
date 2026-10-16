from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from _fixtures import NativeRuntime
from dotenv import load_dotenv
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan import Respan, propagate_attributes
from respan_instrumentation_writer import WriterInstrumentor
from respan_tracing.exporters import RespanSpanExporter
from respan_tracing.exporters.respan import _span_to_otlp_json
from writerai import AsyncWriter, Writer

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
_LOCAL_RUN_ID = "writer-local-" + uuid4().hex[:12]
DEFAULT_WRITER_MODEL = "palmyra-x5"
DEFAULT_WRITER_VISION_MODEL = "palmyra-vision"
DEFAULT_WRITER_TRANSLATION_MODEL = "palmyra-translate"
MOCK_BASE_URL = "https://writer.mock"


def load_root_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def require_respan_api_key() -> str:
    load_root_env()
    api_key = os.getenv("RESPAN_API_KEY")
    if not api_key:
        raise RuntimeError("RESPAN_API_KEY must be set in the repo root .env file")
    return api_key


def respan_base_url() -> str:
    return os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL).rstrip("/")


def model_name() -> str:
    return os.getenv("WRITER_MODEL", DEFAULT_WRITER_MODEL)


def vision_model_name() -> str:
    return os.getenv("WRITER_VISION_MODEL", DEFAULT_WRITER_VISION_MODEL)


def translation_model_name() -> str:
    return os.getenv("WRITER_TRANSLATION_MODEL", DEFAULT_WRITER_TRANSLATION_MODEL)


def writer_api_key() -> str | None:
    return os.getenv("WRITER_API_KEY")


def use_mock_writer() -> bool:
    mode = os.getenv("WRITER_EXAMPLE_MODE", "").strip().lower()
    return mode not in {"live", "real"}


def example_run_id() -> str:
    return os.getenv("RESPAN_EXAMPLE_RUN_ID") or _LOCAL_RUN_ID


def client_mode() -> str:
    return "mock-writer" if use_mock_writer() else "live-writer"


def make_respan(example_name: str, *, capture_content=True) -> Respan:
    export = os.getenv("RESPAN_EXAMPLE_EXPORT") == "1"
    if export:
        load_root_env()
    key = os.environ.pop("RESPAN_API_KEY", None)
    try:
        respan = Respan(
            api_key=None,
            app_name="writer-examples",
            instrumentations=[WriterInstrumentor(capture_content=capture_content)],
            metadata={
                "integration": "writer",
                "example": example_name,
                "example_set": "writer",
                "example_run_id": example_run_id(),
                "run_id": example_run_id(),
            },
            is_auto_instrument=False,
            is_batching_enabled=False,
            log_level="WARNING",
        )
    finally:
        if key is not None:
            os.environ["RESPAN_API_KEY"] = key
    respan.example_memory = InMemorySpanExporter()
    respan.telemetry.add_processor(respan.example_memory, is_batching_enabled=False)
    if export:
        if not key:
            raise RuntimeError("RESPAN_EXAMPLE_EXPORT=1 requires RESPAN_API_KEY")
        respan.telemetry.add_processor(
            RespanSpanExporter(
                endpoint="https://api.respan.ai/api/v2/traces", api_key=key
            ),
            is_batching_enabled=False,
        )
    return respan


def make_client() -> Writer:
    if use_mock_writer():
        return NativeRuntime().client()
    load_root_env()
    key = writer_api_key()
    if not key:
        raise RuntimeError("WRITER_API_KEY is required for explicit live calls")
    return Writer(api_key=key, max_retries=0)


async def make_async_client() -> AsyncWriter:
    if use_mock_writer():
        return NativeRuntime().async_client()
    load_root_env()
    key = writer_api_key()
    if not key:
        raise RuntimeError("WRITER_API_KEY is required for explicit live calls")
    return AsyncWriter(api_key=key, max_retries=0)


def workflow_name(example_name: str) -> str:
    return f"writer_{example_name.replace('-', '_')}"


def make_custom_identifier(example_name: str) -> str:
    return f"writer-{example_name}-{uuid4().hex[:8]}"


@contextmanager
def example_attributes(example_name: str, custom_identifier: str | None = None):
    custom_identifier = custom_identifier or make_custom_identifier(example_name)
    current_workflow_name = workflow_name(example_name)
    with propagate_attributes(
        custom_identifier=custom_identifier,
        trace_group_identifier=current_workflow_name,
        metadata={
            "example": example_name,
            "example_set": "writer",
            "example_run_id": example_run_id(),
            "run_id": example_run_id(),
            "workflow_name": current_workflow_name,
            "client_mode": client_mode(),
        },
    ):
        yield custom_identifier


def graph_ids() -> list[str]:
    value = os.getenv("WRITER_GRAPH_IDS") or os.getenv("WRITER_GRAPH_ID")
    if value:
        return [item.strip() for item in value.split(",") if item.strip()]
    if use_mock_writer():
        return ["graph_mock"]
    raise RuntimeError(
        "Set WRITER_GRAPH_ID or WRITER_GRAPH_IDS for live graph examples"
    )


def application_id() -> str:
    value = os.getenv("WRITER_APPLICATION_ID")
    if value:
        return value
    if use_mock_writer():
        return "app_mock"
    raise RuntimeError("Set WRITER_APPLICATION_ID for live application examples")


def file_id() -> str:
    value = os.getenv("WRITER_FILE_ID") or os.getenv("WRITER_VISION_FILE_ID")
    if value:
        return value
    if use_mock_writer():
        return "file_mock"
    raise RuntimeError(
        "Set WRITER_FILE_ID or WRITER_VISION_FILE_ID for live file examples"
    )


def print_start(example_name: str, custom_identifier: str) -> None:
    print(f"example={example_name}", flush=True)
    print(f"custom_identifier={custom_identifier}", flush=True)
    print(f"workflow_name={workflow_name(example_name)}", flush=True)
    print(f"client_mode={client_mode()}", flush=True)
    print(f"example_run_id={example_run_id()}", flush=True)


def print_result(label: str, value: Any) -> None:
    print(f"\n== {label} ==")
    if isinstance(value, str):
        print(value.strip())
        return
    print(json.dumps(value, default=str, indent=2, sort_keys=True))


def finish_respan(respan: Respan) -> None:
    try:
        respan.flush()
        directory = os.getenv("RESPAN_EXAMPLE_REPORT_DIR")
        if directory:
            import sys

            folder = Path(directory)
            folder.mkdir(parents=True, exist_ok=True)
            (folder / (Path(sys.argv[0]).stem + ".json")).write_text(
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


def close_client(client: Writer) -> None:
    client.close()


async def close_async_client(client: AsyncWriter) -> None:
    await client.close()
