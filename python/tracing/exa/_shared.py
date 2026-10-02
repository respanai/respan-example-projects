from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from _mock_server import run_mock_exa_server
from dotenv import load_dotenv
from exa_py import AsyncExa, Exa
from respan import Respan, propagate_attributes
from respan_instrumentation_exa import ExaInstrumentor

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"


def load_root_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def require_env(name: str) -> str:
    load_root_env()
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set in the repository root .env file")
    return value


def run_id() -> str:
    value = os.getenv("RESPAN_EXAMPLE_RUN_ID")
    if not value:
        raise RuntimeError("RESPAN_EXAMPLE_RUN_ID must be supplied by run_all.py")
    return value


def use_live_exa() -> bool:
    return os.getenv("RESPAN_EXA_LIVE", "0").lower() in {"1", "true", "yes"}


def make_respan(example_name: str) -> Respan:
    return Respan(
        api_key=require_env("RESPAN_API_KEY"),
        base_url=os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL),
        app_name="exa-python-examples",
        instrumentations=[ExaInstrumentor()],
        metadata={
            "example_set": "python/tracing/exa",
            "example": example_name,
            "run_id": run_id(),
        },
    )


@contextmanager
def clients() -> Iterator[tuple[Exa, AsyncExa, str]]:
    load_root_env()
    if use_live_exa():
        key = require_env("EXA_API_KEY")
        yield Exa(api_key=key), AsyncExa(api_key=key), "live"
        return
    with run_mock_exa_server() as base_url:
        yield (
            Exa(api_key="loopback-exa-key", base_url=base_url),
            AsyncExa(api_key="loopback-exa-key", api_base=base_url),
            "loopback",
        )


@contextmanager
def example_attributes(example_name: str, mode: str):
    workflow_name = f"exa_python_{example_name.replace('-', '_')}"
    with propagate_attributes(
        custom_identifier=f"exa-{example_name}-{run_id()}",
        trace_group_identifier=workflow_name,
        metadata={
            "example": example_name,
            "example_set": "python/tracing/exa",
            "run_id": run_id(),
            "workflow_name": workflow_name,
            "exa_mode": mode,
        },
    ):
        yield workflow_name


def finish(respan: Respan) -> None:
    try:
        respan.flush()
    finally:
        respan.shutdown()
