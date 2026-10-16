"""Shared helpers for Braintrust Respan examples."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

import braintrust
from dotenv import load_dotenv
from respan import Respan
from respan_instrumentation_braintrust import BraintrustInstrumentor

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]
ROOT_ENV = REPO_ROOT / ".env"
CUSTOMER_IDENTIFIER = "braintrust-example"


def load_repo_env() -> None:
    """Load the example repository root .env without introducing extra deps."""
    load_dotenv(ROOT_ENV, override=False)


def new_run_id(example_name: str) -> str:
    return (
        os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"{example_name}-{uuid.uuid4().hex[:10]}"
    )


def create_respan(*, workflow_name: str, run_id: str, example_name: str) -> Respan:
    load_repo_env()
    return Respan(
        api_key=os.getenv("RESPAN_API_KEY") or os.getenv("RESPAN_GATEWAY_API_KEY"),
        base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
        app_name="braintrust-example",
        instrumentations=[BraintrustInstrumentor()],
        customer_identifier=CUSTOMER_IDENTIFIER,
        metadata={
            "example_set": "braintrust",
            "example_name": example_name,
            "workflow_name": workflow_name,
            "run_id": run_id,
        },
        environment="example",
        is_batching_enabled=False,
    )


def create_braintrust_logger(*, workflow_name: str) -> braintrust.Logger:
    braintrust._internal_get_global_state()._override_bg_logger.logger = FixtureSink()
    return braintrust.init_logger(
        project="Respan Braintrust Examples",
        project_id=f"respan-braintrust-{workflow_name.lower().replace(' ', '-')}",
        api_key=getattr(braintrust.logger, "TEST_API_KEY", "___TEST_API_KEY__"),
        async_flush=False,
        set_current=False,
    )


def workflow_context(
    respan: Respan,
    *,
    workflow_name: str,
    run_id: str,
    example_name: str,
) -> Any:
    return respan.propagate_attributes(
        trace_group_identifier=f"{workflow_name}-{run_id}",
        custom_identifier=run_id,
        metadata={
            "example_set": "braintrust",
            "example_name": example_name,
            "workflow_name": workflow_name,
            "run_id": run_id,
        },
    )


def print_trace_lookup(*, workflow_name: str, run_id: str) -> None:
    print(f"workflow_name={workflow_name}")
    print(f"RESPAN_EXAMPLE_RUN_ID={run_id}")


def flush_and_shutdown(respan: Respan, logger: braintrust.Logger) -> None:
    logger.flush()
    respan.shutdown()


class FixtureSink:
    """Resolve released SDK records locally without contacting Braintrust."""

    def __init__(self):
        self.rows = []

    def log(self, *rows):
        self.rows.extend(rows)

    def flush(self, *args, **kwargs):
        rows, self.rows = self.rows, []
        for row in rows:
            row.get()

    def enforce_queue_size_limit(self, enforce):
        pass

    def set_masking_function(self, masking):
        self._masking_function = masking
