"""Shared setup for local Guardrails fixtures and Respan trace export."""

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

# Keep LiteLLM's model-cost lookup local even when using its mock responses.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from dotenv import load_dotenv
from guardrails.settings import settings
from opentelemetry.semconv_ai import SpanAttributes
from respan import Respan, get_client, propagate_attributes
from respan_instrumentation_guardrails import GuardrailsInstrumentor


def make_respan(app_name: str) -> tuple[Respan, str]:
    load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)
    settings.rc.enable_metrics = False
    settings.disable_tracing = False
    instrumentor = GuardrailsInstrumentor()
    respan = Respan(
        api_key=os.environ["RESPAN_API_KEY"],
        base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
        app_name=app_name,
        instrumentations=[instrumentor],
        is_auto_instrument=False,
        is_batching_enabled=False,
    )
    if not instrumentor.is_instrumented:
        respan.shutdown()
        raise RuntimeError("Guardrails instrumentation did not activate")
    return respan, os.getenv("RESPAN_MODEL", "gpt-4o-mini")


@contextmanager
def example_attributes(
    example_name: str,
    workflow_name: str,
    *,
    customer_identifier: str | None = None,
    thread_identifier: str | None = None,
):
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"guardrails-{uuid4().hex[:12]}"
    attributes: dict[str, Any] = {
        "custom_identifier": f"{run_id}:{example_name}",
        "trace_group_identifier": workflow_name,
        "metadata": {
            "example": example_name,
            "run_id": run_id,
            "workflow_name": workflow_name,
        },
    }
    if customer_identifier is not None:
        attributes["customer_identifier"] = customer_identifier
    if thread_identifier is not None:
        attributes["thread_identifier"] = thread_identifier
    with propagate_attributes(**attributes):
        yield run_id


def set_workflow_input(payload: dict[str, Any]) -> None:
    if os.getenv("TRACELOOP_TRACE_CONTENT", "true").lower() != "true":
        return
    get_client().update_current_span(
        attributes={
            SpanAttributes.TRACELOOP_ENTITY_INPUT: json.dumps(payload, default=str)
        }
    )


def result_summary(result: Any) -> dict[str, Any]:
    return {
        "validation_passed": bool(getattr(result, "validation_passed", False)),
        "validated_output": getattr(result, "validated_output", None),
        "raw_llm_output": getattr(result, "raw_llm_output", None),
        "error": getattr(result, "error", None),
    }


def local_guard(guard):
    """Disable Guardrails Hub telemetry for these local validation examples."""
    guard.configure(allow_metrics_collection=False)
    settings.rc.enable_metrics = False
    return guard
