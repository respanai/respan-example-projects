"""Fixture-first setup; provider calls and trace export are explicit choices."""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
from _fixtures import MODEL as fixture_model
from _fixtures import reply
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from openrouter import OpenRouter
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan_instrumentation_openrouter import OpenRouterInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_METADATA
from respan_tracing import RespanTelemetry
from respan_tracing import tool as native_tool
from respan_tracing import workflow as native_workflow
from respan_tracing.exporters import RespanSpanExporter
from respan_tracing.exporters.respan import _span_to_otlp_json

MODEL = fixture_model
workflow = native_workflow
tool = native_tool


def _load_env_file(path):
    load_dotenv(path, override=False)


def run_id():
    return (
        os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"otel2-openrouter-local-{time.time_ns()}"
    )


class Tags(SpanProcessor):
    def __init__(self, marker, scenario):
        self.metadata = {
            "run_id": marker,
            "example_run_id": marker,
            "scenario": scenario,
            "example_set": "python/tracing/openrouter",
        }

    def on_start(self, span, parent_context=None):
        for key, value in self.metadata.items():
            span.set_attribute(f"{RESPAN_METADATA}.{key}", value)

    def on_end(self, span):
        pass


@contextmanager
def tracing(scenario, *, capture_content=True):
    _load_env_file(Path(__file__).resolve().parents[3] / ".env")
    # RespanTelemetry reads environment credentials; suppress its default exporter
    # so only the explicit export option can send data.
    api_key = os.environ.pop("RESPAN_API_KEY", None)
    try:
        telemetry = RespanTelemetry(
            app_name="openrouter-examples",
            api_key=None,
            is_auto_instrument=False,
            is_batching_enabled=False,
            log_level="WARNING",
        )
    finally:
        if api_key is not None:
            os.environ["RESPAN_API_KEY"] = api_key
    provider = telemetry.tracer.tracer_provider
    memory = InMemorySpanExporter()
    telemetry.add_processor(memory, is_batching_enabled=False)
    provider.add_span_processor(Tags(run_id(), scenario))
    inst = OpenRouterInstrumentor(capture_content=capture_content)
    inst.activate()
    if not inst._is_instrumented:
        raise RuntimeError("OpenRouter instrumentation did not activate")
    if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
        if not api_key:
            raise RuntimeError("RESPAN_EXAMPLE_EXPORT=1 requires RESPAN_API_KEY")
        telemetry.add_processor(
            RespanSpanExporter(
                endpoint="https://api.respan.ai/api/v2/traces", api_key=api_key
            ),
            is_batching_enabled=False,
        )
    try:
        yield memory
    finally:
        telemetry.flush()
        report_dir = os.getenv("RESPAN_EXAMPLE_REPORT_DIR")
        if report_dir:
            path = Path(report_dir)
            path.mkdir(parents=True, exist_ok=True)
            (path / f"openrouter-{scenario}.json").write_text(
                json.dumps(
                    [_span_to_otlp_json(s) for s in memory.get_finished_spans()],
                    indent=2,
                ),
                encoding="utf-8",
            )
        inst.deactivate()
        provider.shutdown()


class NativeContext:
    def __init__(self, sdk, transport, asynchronous):
        self.sdk, self.transport, self.asynchronous = sdk, transport, asynchronous

    def __enter__(self):
        return self.sdk.__enter__()

    def __exit__(self, *args):
        try:
            return self.sdk.__exit__(*args)
        finally:
            self.transport.close()

    async def __aenter__(self):
        return await self.sdk.__aenter__()

    async def __aexit__(self, *args):
        try:
            return await self.sdk.__aexit__(*args)
        finally:
            await self.transport.aclose()


def native_client(*, live=False, asynchronous=False):
    if live:
        if os.getenv("OPENROUTER_EXAMPLE_LIVE") != "1":
            raise RuntimeError("Live provider calls require OPENROUTER_EXAMPLE_LIVE=1")
        key = os.environ["OPENROUTER_API_KEY"]
        return OpenRouter(api_key=key)
    transport = (
        httpx.AsyncClient(transport=httpx.MockTransport(reply))
        if asynchronous
        else httpx.Client(transport=httpx.MockTransport(reply))
    )
    sdk = OpenRouter(
        api_key="fixture-key",
        **({"async_client": transport} if asynchronous else {"client": transport}),
    )
    return NativeContext(sdk, transport, asynchronous)


def compatible_client(*, asynchronous=False):
    transport = httpx.MockTransport(reply)
    return (
        AsyncOpenAI(
            api_key="fixture-key",
            base_url="https://openrouter.ai/api/v1",
            http_client=httpx.AsyncClient(transport=transport),
            max_retries=0,
        )
        if asynchronous
        else OpenAI(
            api_key="fixture-key",
            base_url="https://openrouter.ai/api/v1",
            http_client=httpx.Client(transport=transport),
            max_retries=0,
        )
    )
