"""Shared setup; controlled fixtures run without credentials by default."""

from __future__ import annotations

import os
from pathlib import Path

from _fixture import create_fixture_model
from dotenv import load_dotenv
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan import Respan
from respan_instrumentation_strands_agents import StrandsAgentsInstrumentor
from strands.models.openai import OpenAIModel

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]


def load_example_environment() -> tuple[str, str, str]:
    invocation_marker = os.getenv("RESPAN_EXAMPLE_RUN_ID")
    load_dotenv(REPO_ROOT / ".env", override=False)
    if invocation_marker:
        os.environ["RESPAN_EXAMPLE_RUN_ID"] = invocation_marker
    return (
        os.environ["RESPAN_API_KEY"],
        os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api").rstrip("/"),
        os.getenv("RESPAN_STRANDS_MODEL", "gpt-4o-mini"),
    )


def create_gateway_model(
    *, model_id: str | None = None, base_url: str | None = None
) -> OpenAIModel:
    if os.getenv("RESPAN_STRANDS_LIVE") != "1":
        return create_fixture_model(fail=base_url is not None)
    key, url, default_model = load_example_environment()
    return OpenAIModel(
        model_id=model_id or default_model,
        client_args={
            "api_key": key,
            "base_url": base_url or url,
            "max_retries": 0,
            "timeout": 15,
        },
    )


def create_respan(example_name: str, run_id: str) -> Respan:
    exporting = (
        os.getenv("RESPAN_STRANDS_EXPORT") == "1"
        or os.getenv("RESPAN_STRANDS_LIVE") == "1"
    )
    key, url, _ = (
        load_example_environment()
        if exporting
        else (None, "https://api.respan.ai/api", None)
    )
    previous_key = os.environ.pop("RESPAN_API_KEY", None) if not exporting else None
    try:
        respan = Respan(
            api_key=key,
            base_url=url,
            app_name=f"strands-agents-{example_name}",
            instrumentations=[StrandsAgentsInstrumentor()],
            metadata={
                "example": example_name,
                "run_id": run_id,
                "example_run_id": run_id,
                "example_set": "strands-agents",
                "framework": "strands-agents",
            },
            environment="examples",
        )
        if not exporting:
            respan.telemetry.add_processor(exporter=InMemorySpanExporter())
        return respan
    finally:
        if previous_key is not None:
            os.environ["RESPAN_API_KEY"] = previous_key


def new_run_id(example_name: str) -> str:
    return os.getenv("RESPAN_EXAMPLE_RUN_ID", f"strands-{example_name}-local")


def finish_respan(respan: Respan) -> None:
    try:
        respan.flush()
    finally:
        respan.shutdown()
