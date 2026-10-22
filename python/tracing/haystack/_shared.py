"""Shared helpers for Haystack tracing examples."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import find_dotenv, load_dotenv

_CURRENT_APP_NAME = "haystack-example"
_LAST_RESULT_LABEL = ""
_LAST_RESULT_JSON = "{}"
_CURRENT_WORKFLOW_CONTEXT = None
_CURRENT_WORKFLOW_SPAN = None
_CURRENT_ATTRIBUTE_CONTEXT = None


def configure_respan(app_name: str, *, use_gateway: bool = False, config=None):
    """Initialize Respan Haystack instrumentation.

    When RESPAN_API_KEY is absent, Respan still initializes local OpenTelemetry
    instrumentation but skips export, which keeps most examples runnable offline.
    Gateway examples require RESPAN_API_KEY because they call the Respan gateway.
    """
    global _CURRENT_APP_NAME

    _CURRENT_APP_NAME = app_name
    load_dotenv(find_dotenv(), override=False)
    os.environ.setdefault("HAYSTACK_TELEMETRY_ENABLED", "false")
    os.environ.setdefault("HAYSTACK_CONTENT_TRACING_ENABLED", "true")

    api_key = os.getenv("RESPAN_API_KEY")
    base_url = os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api")

    if use_gateway:
        if not api_key:
            raise RuntimeError("RESPAN_API_KEY is required for gateway examples.")
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = base_url

    from respan import Respan, get_client
    from respan_instrumentation_haystack import HaystackInstrumentor

    instrumentor = HaystackInstrumentor(
        **({"config": config} if config is not None else {})
    )
    respan = Respan(
        api_key=api_key,
        base_url=base_url,
        app_name=app_name,
        instrumentations=[instrumentor],
        is_batching_enabled=False,
        log_level=os.getenv("RESPAN_LOG_LEVEL", "WARNING"),
    )
    if not instrumentor.is_instrumented:
        respan.shutdown()
        raise RuntimeError("Haystack instrumentation did not activate")

    _start_example_workflow(app_name, get_client())
    return respan


def finish_respan(respan: Any, *, emit_summary_span: bool = True) -> None:
    if respan is None:
        return
    if emit_summary_span:
        try:
            _emit_example_run_span()
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to emit example run span: {exc}")
    _finish_example_workflow()
    shutdown = getattr(respan, "shutdown", None)
    if shutdown is not None:
        shutdown()


def print_result(label: str, value: Any) -> None:
    global _LAST_RESULT_LABEL, _LAST_RESULT_JSON

    _LAST_RESULT_LABEL = label
    _LAST_RESULT_JSON = json.dumps(value, default=str, indent=2, sort_keys=True)
    print(f"\n== {label} ==")
    print(_LAST_RESULT_JSON)


def _start_example_workflow(app_name: str, client: Any) -> None:
    global _CURRENT_ATTRIBUTE_CONTEXT, _CURRENT_WORKFLOW_CONTEXT, _CURRENT_WORKFLOW_SPAN

    _finish_example_workflow()
    from respan import propagate_attributes

    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"haystack-{uuid4().hex[:12]}"
    _CURRENT_ATTRIBUTE_CONTEXT = propagate_attributes(
        custom_identifier=f"haystack-{app_name}-{uuid4().hex[:8]}",
        trace_group_identifier=app_name,
        metadata={
            "example": app_name,
            "run_id": run_id,
            "workflow_name": app_name,
        },
    )
    _CURRENT_ATTRIBUTE_CONTEXT.__enter__()
    _CURRENT_WORKFLOW_CONTEXT = client.start_span(app_name, kind="workflow")
    _CURRENT_WORKFLOW_SPAN = _CURRENT_WORKFLOW_CONTEXT.__enter__()
    if _CURRENT_WORKFLOW_SPAN is not None:
        _CURRENT_WORKFLOW_SPAN.set_attribute(
            "traceloop.entity.input",
            json.dumps({"example": app_name}, separators=(",", ":")),
        )


def _finish_example_workflow() -> None:
    global _CURRENT_ATTRIBUTE_CONTEXT, _CURRENT_WORKFLOW_CONTEXT, _CURRENT_WORKFLOW_SPAN

    if _CURRENT_WORKFLOW_CONTEXT is None:
        return
    try:
        if _CURRENT_WORKFLOW_SPAN is not None:
            _CURRENT_WORKFLOW_SPAN.set_attribute(
                "traceloop.entity.output",
                _LAST_RESULT_JSON[:4000],
            )
        _CURRENT_WORKFLOW_CONTEXT.__exit__(None, None, None)
    finally:
        _CURRENT_WORKFLOW_CONTEXT = None
        _CURRENT_WORKFLOW_SPAN = None
        if _CURRENT_ATTRIBUTE_CONTEXT is not None:
            _CURRENT_ATTRIBUTE_CONTEXT.__exit__(None, None, None)
            _CURRENT_ATTRIBUTE_CONTEXT = None


def _emit_example_run_span() -> None:
    from respan_tracing.decorators import task

    @task(name="haystack.example.run")
    def record_example_run() -> dict[str, str]:
        return {
            "example": _CURRENT_APP_NAME,
            "result_label": _LAST_RESULT_LABEL,
            "result_preview": _LAST_RESULT_JSON[:4000],
        }

    record_example_run()


def sample_documents():
    from haystack import Document

    return [
        Document(
            content="Python was created by Guido van Rossum and first released in 1991.",
            meta={"kind": "programming", "mime": "text/plain", "source": "python"},
            score=0.92,
            embedding=[0.9, 0.1, 0.0],
        ),
        Document(
            content="Rust is a systems programming language focused on safety and performance.",
            meta={"kind": "programming", "mime": "text/plain", "source": "rust"},
            score=0.73,
            embedding=[0.7, 0.3, 0.0],
        ),
        Document(
            content="Pasta water should be salted before the noodles are added.",
            meta={"kind": "cooking", "mime": "text/plain", "source": "pasta"},
            score=0.35,
            embedding=[0.1, 0.9, 0.0],
        ),
    ]


def sample_document_store():
    from haystack.document_stores.in_memory import InMemoryDocumentStore

    store = InMemoryDocumentStore()
    store.write_documents(sample_documents())
    return store


def write_sample_files(directory: Path) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    files = {
        "csv": directory / "sample.csv",
        "json": directory / "sample.json",
        "markdown": directory / "sample.md",
        "text": directory / "sample.txt",
        "html": directory / "sample.html",
    }
    files["csv"].write_text("text,kind\nalpha row,a\nbeta row,b\n", encoding="utf-8")
    files["json"].write_text(
        '[{"text": "json row", "kind": "json"}]',
        encoding="utf-8",
    )
    files["markdown"].write_text("# Title\n\nMarkdown body.", encoding="utf-8")
    files["text"].write_text("Plain text body.", encoding="utf-8")
    files["html"].write_text(
        "<html><body><main><h1>HTML title</h1><p>HTML body.</p></main></body></html>",
        encoding="utf-8",
    )
    return files


def create_tool_runner(tools):
    """Use the current Agent-owned executor, or ToolInvoker on Haystack 2."""
    try:
        from haystack.components.tools import ToolInvoker
    except ImportError:
        from haystack.components.agents import Agent
        from haystack.components.generators.chat import MockChatGenerator

        return Agent(
            chat_generator=MockChatGenerator(response_fn=_tool_response),
            tools=tools,
            raise_on_tool_invocation_failure=True,
        )
    return ToolInvoker(tools)


def _tool_response(messages):
    from haystack.dataclasses import ChatMessage

    if any(message.tool_call_results for message in messages):
        return ChatMessage.from_assistant("Tool completed")
    return next(message for message in reversed(messages) if message.tool_calls)
