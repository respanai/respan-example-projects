"""Shared setup for deterministic AgentSpec tracing examples."""

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from respan import Respan, propagate_attributes
from respan_instrumentation_agentspec import AgentSpecInstrumentor

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUN_ID = datetime.now(timezone.utc).strftime("agentspec-%Y%m%d-%H%M%S")


def run_id():
    load_dotenv(REPO_ROOT / ".env", override=False)
    return os.getenv("RESPAN_EXAMPLE_RUN_ID", DEFAULT_RUN_ID)


def build_respan(example_name, *, mask_sensitive_information=False):
    marker = run_id()
    key = os.getenv("RESPAN_API_KEY")
    if not key:
        raise RuntimeError("RESPAN_API_KEY is required for trace export")
    return Respan(
        api_key=key,
        base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
        app_name="agentspec-" + example_name,
        instrumentations=[
            AgentSpecInstrumentor(
                workflow_name="agentspec_" + example_name.replace("-", "_"),
                mask_sensitive_information=mask_sensitive_information,
            )
        ],
        metadata={
            "run_id": marker,
            "integration": "agentspec",
            "example": example_name,
        },
        environment="examples",
        is_batching_enabled=False,
    )


@contextmanager
def example_scope(example_name, **attributes):
    with propagate_attributes(
        trace_group_identifier="agentspec-" + example_name,
        metadata={
            "run_id": run_id(),
            "integration": "agentspec",
            "example": example_name,
        },
        **attributes,
    ):
        yield


def latest_message_content(result):
    latest = result["messages"][-1]
    return latest.content if hasattr(latest, "content") else latest["content"]
