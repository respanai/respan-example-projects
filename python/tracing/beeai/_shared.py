"""Fixture mode is local by default; export and provider calls are explicit."""

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan import Respan, propagate_attributes
from respan_instrumentation_beeai import BeeAIInstrumentor

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
DEFAULT_BEEAI_MODEL = "openai:gpt-4.1-nano"


def live_mode() -> bool:
    return os.getenv("BEEAI_EXAMPLE_MODE", "fixture") == "live"


def create_respan(app_name: str) -> Respan:
    export = os.getenv("RESPAN_EXAMPLE_EXPORT") == "1"
    if export or live_mode():
        load_dotenv(
            Path(os.getenv("RESPAN_EXAMPLE_ENV_FILE", REPO_ROOT / ".env")),
            override=False,
        )
    # Respan falls back to the environment even for api_key="". Keep local mode offline.
    existing_key = os.environ.pop("RESPAN_API_KEY", None) if not export else None
    try:
        respan = Respan(
            app_name=app_name,
            api_key=os.environ["RESPAN_API_KEY"] if export else None,
            base_url=os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL),
            instrumentations=[BeeAIInstrumentor()],
            is_batching_enabled=False,
            log_level="WARNING",
        )
    finally:
        if existing_key is not None:
            os.environ["RESPAN_API_KEY"] = existing_key
    if not export:
        respan.telemetry.add_processor(
            InMemorySpanExporter(), name="beeai-local", is_batching_enabled=False
        )
    return respan


def get_chat_model(*, mode: str = "text", error: bool = False):
    if live_mode():
        from beeai_framework.backend import ChatModel

        return ChatModel.from_name(
            "openai:gpt-this-model-does-not-exist"
            if error
            else os.getenv("BEEAI_MODEL", DEFAULT_BEEAI_MODEL)
        )
    from _fixtures import FixtureChatModel

    return FixtureChatModel(mode=mode, error=error)


@contextmanager
def example_attributes(workflow_name: str) -> Iterator[str]:
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID", f"beeai-{uuid.uuid4().hex[:10]}")
    with propagate_attributes(
        group_identifier=workflow_name,
        custom_identifier=run_id,
        metadata={
            "framework": "beeai",
            "example": workflow_name,
            "run_id": run_id,
            "mode": "live" if live_mode() else "fixture",
        },
    ):
        yield run_id
