"""Shared Helicone example setup with exact marker propagation."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from _local_sink import endpoint, received, reset, shutdown
from dotenv import load_dotenv
from helicone_helpers import HeliconeManualLogger
from respan import Respan, propagate_attributes
from respan_instrumentation_helicone import HeliconeInstrumentor

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]
DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
EXAMPLE_SET = "helicone"


def load_root_env() -> None:
    load_dotenv(REPO_ROOT / ".env", override=False)
    if not os.getenv("RESPAN_API_KEY"):
        raise RuntimeError(f"RESPAN_API_KEY is required in {REPO_ROOT / '.env'}")


def marker() -> str:
    return os.getenv("RESPAN_EXAMPLE_RUN_ID", "").strip() or (
        f"helicone-{uuid4().hex[:10]}"
    )


def execution_id() -> str:
    return uuid4().hex[:10]


def workflow_name(example_name: str) -> str:
    return f"helicone_{example_name.replace('-', '_')}"


def make_respan(
    example_name: str, run_marker: str, *, capture_content: bool = True
) -> Respan:
    load_root_env()
    return Respan(
        api_key=os.environ["RESPAN_API_KEY"],
        base_url=os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL),
        app_name=workflow_name(example_name),
        instrumentations=[HeliconeInstrumentor(capture_content=capture_content)],
        is_batching_enabled=False,
        metadata={
            "example_set": EXAMPLE_SET,
            "workflow_name": workflow_name(example_name),
            "example_run_id": run_marker,
            "run_id": run_marker,
        },
        log_level=os.getenv("RESPAN_LOG_LEVEL", "WARNING"),
    )


def make_logger(
    *, live: bool = False, headers: dict[str, str] | None = None
) -> HeliconeManualLogger:
    load_root_env()
    if live:
        api_key = os.getenv("HELICONE_API_KEY")
        if not api_key:
            raise RuntimeError("HELICONE_API_KEY is required for the live example")
        return HeliconeManualLogger(api_key=api_key, headers=headers or {})
    reset()
    return HeliconeManualLogger(
        api_key="local-helicone-example-key",
        headers=headers or {},
        logging_endpoint=endpoint(),
    )


def live_configured() -> bool:
    load_root_env()
    return bool(os.getenv("HELICONE_API_KEY"))


@contextmanager
def example_attributes(
    example_name: str, run_marker: str, execution: str, *, mode: str
):
    current_workflow = workflow_name(example_name)
    with propagate_attributes(
        custom_identifier=f"{current_workflow}-{execution}",
        trace_group_identifier=current_workflow,
        metadata={
            "example_set": EXAMPLE_SET,
            "example": example_name,
            "workflow_name": current_workflow,
            "example_run_id": run_marker,
            "run_id": run_marker,
            "execution_id": execution,
            "mode": mode,
        },
    ):
        yield


def assert_local_logs(expected: int, *, path_suffix: str = "/custom/v1/log") -> None:
    logs = received()
    if len(logs) != expected:
        raise AssertionError(
            f"expected {expected} local Helicone logs, received {len(logs)}"
        )
    if any(not item["path"].endswith(path_suffix) for item in logs):
        raise AssertionError([item["path"] for item in logs])


def print_result(example_name: str, run_marker: str, result: Any) -> None:
    print(f"RESPAN_EXAMPLE_RUN_ID={run_marker}")
    print(f"\n== {example_name} ==")
    print(json.dumps(result, allow_nan=False, indent=2, sort_keys=True))


def finish_respan(respan: Respan) -> None:
    try:
        respan.flush()
    finally:
        try:
            respan.shutdown()
        finally:
            shutdown()
