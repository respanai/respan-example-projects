"""Shared helpers for the LlamaIndex Respan examples."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from _fixture import build_fixture_embedding, build_fixture_llm
from dotenv import load_dotenv
from llama_index.core import Document, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv_ai import SpanAttributes
from respan import Respan
from respan_instrumentation_llama_index import LlamaIndexInstrumentor


@dataclass(frozen=True)
class GatewaySettings:
    api_key: str
    base_url: str
    model: str
    embedding_model: str


@dataclass(frozen=True)
class ExampleContext:
    respan: Respan
    settings: GatewaySettings
    example_name: str
    run_id: str


@dataclass(frozen=True)
class ExampleSpan:
    span: Any | None

    def set_input(self, value: object) -> None:
        self._set_json_attribute(
            attribute=SpanAttributes.TRACELOOP_ENTITY_INPUT,
            value=value,
        )

    def set_output(self, value: object) -> None:
        self._set_json_attribute(
            attribute=SpanAttributes.TRACELOOP_ENTITY_OUTPUT,
            value=value,
        )

    def _set_json_attribute(self, *, attribute: str, value: object) -> None:
        if self.span is not None:
            self.span.set_attribute(attribute, json.dumps(value, default=str))


def load_gateway_settings() -> GatewaySettings:
    if os.getenv("RESPAN_LLAMA_INDEX_LIVE") != "1":
        return GatewaySettings(
            api_key="fixture-key",
            base_url="https://fixture.invalid/v1",
            model="gpt-4o-mini",
            embedding_model="text-embedding-3-large",
        )
    _load_env_files()
    api_key = os.environ["RESPAN_API_KEY"]
    base_url = os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api")
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = base_url
    os.environ["OPENAI_API_BASE"] = base_url
    return GatewaySettings(
        api_key=api_key,
        base_url=base_url,
        model=os.getenv("RESPAN_MODEL", "gpt-4o-mini"),
        embedding_model=os.getenv("RESPAN_EMBEDDING_MODEL", "text-embedding-3-small"),
    )


def create_respan(
    *,
    app_name: str,
    example_name: str,
    capture_content: bool = True,
    **kwargs,
) -> ExampleContext:
    settings = load_gateway_settings()
    run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID") or uuid4().hex[:8]
    metadata = {
        "example_set": "llama-index",
        "example_name": example_name,
        "example_run_id": run_id,
        "run_id": run_id,
    }
    metadata.update(kwargs.pop("metadata", {}))
    exporting = (
        os.getenv("RESPAN_LLAMA_INDEX_EXPORT") == "1"
        or os.getenv("RESPAN_LLAMA_INDEX_LIVE") == "1"
    )
    if exporting:
        _load_env_files()
    export_key = os.environ.get("RESPAN_API_KEY") if exporting else None
    previous_key = os.environ.pop("RESPAN_API_KEY", None) if not exporting else None
    try:
        respan = Respan(
            app_name=app_name,
            api_key=export_key,
            base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
            metadata=metadata,
            instrumentations=[
                LlamaIndexInstrumentor(capture_content=capture_content),
            ],
            **kwargs,
        )
    finally:
        if previous_key is not None:
            os.environ["RESPAN_API_KEY"] = previous_key
    if not exporting:
        respan.telemetry.add_processor(exporter=InMemorySpanExporter())
    return ExampleContext(
        respan=respan,
        settings=settings,
        example_name=example_name,
        run_id=run_id,
    )


@contextmanager
def traced_example(
    context: ExampleContext,
    *,
    root_span_name: str | None = None,
    input_data: object | None = None,
):
    """Propagate the exact run marker and flush after each example."""

    try:
        with context.respan.propagate_attributes(
            trace_group_identifier=f"{context.example_name}-{context.run_id}",
            custom_identifier=f"{context.example_name}-{context.run_id}",
            metadata={
                "example_set": "llama-index",
                "example_name": context.example_name,
                "example_run_id": context.run_id,
                "run_id": context.run_id,
            },
        ):
            if root_span_name is None:
                yield ExampleSpan(span=None)
                return

            client = context.respan.telemetry.get_client()
            with client.start_span(root_span_name, kind="workflow") as span:
                example_span = ExampleSpan(span=span)
                if input_data is not None:
                    example_span.set_input(input_data)
                yield example_span
    finally:
        try:
            context.respan.flush()
        finally:
            context.respan.shutdown()


def configure_llama_index(settings: GatewaySettings) -> None:
    Settings.llm = build_llm(settings)
    Settings.embed_model = build_embedding_model(settings)


def build_llm(settings: GatewaySettings) -> OpenAI:
    if os.getenv("RESPAN_LLAMA_INDEX_LIVE") != "1":
        return build_fixture_llm()
    return OpenAI(
        model=settings.model,
        api_key=settings.api_key,
        api_base=settings.base_url,
        max_retries=0,
    )


def build_embedding_model(settings: GatewaySettings) -> OpenAIEmbedding:
    if os.getenv("RESPAN_LLAMA_INDEX_LIVE") != "1":
        return build_fixture_embedding()
    return OpenAIEmbedding(
        model=settings.embedding_model,
        api_key=settings.api_key,
        api_base=settings.base_url,
        max_retries=0,
    )


def sample_documents() -> list[Document]:
    return [
        Document(
            text=(
                "Respan captures traces for LLM calls, tool calls, and workflow "
                "steps so teams can inspect application behavior."
            )
        ),
        Document(
            text=(
                "LlamaIndex applications often combine query engines, retrievers, "
                "agents, and tools into one request path."
            )
        ),
    ]


def print_result(label: str, value: object) -> None:
    print(f"{label}: {value}")


def _load_env_files() -> None:
    invocation_run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID", "").strip()
    for env_path in _env_paths_from(start=Path(__file__).resolve().parent):
        load_dotenv(env_path, override=False)
    for env_path in _env_paths_from(start=Path.cwd()):
        load_dotenv(env_path, override=False)
    if invocation_run_id:
        os.environ["RESPAN_EXAMPLE_RUN_ID"] = invocation_run_id


def _env_paths_from(*, start: Path) -> Iterable[Path]:
    current = start.resolve()
    chain: list[Path] = []
    while True:
        chain.append(current)
        if (current / ".git").exists():
            break
        if current.parent == current:
            break
        current = current.parent

    seen: set[Path] = set()
    for directory in reversed(chain):
        env_path = directory / ".env"
        if env_path.exists() and env_path not in seen:
            seen.add(env_path)
            yield env_path
