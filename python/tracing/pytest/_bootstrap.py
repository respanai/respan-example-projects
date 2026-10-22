"""Initialize released OTel/exporter before the installed pytest entry point."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_provider = None
_memory = None
_wire = []


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    global _provider, _memory
    _provider = TracerProvider()
    _memory = InMemorySpanExporter()
    _provider.add_span_processor(SimpleSpanProcessor(_memory))
    if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
        from dotenv import load_dotenv
        from respan_tracing.exporters import RespanSpanExporter

        load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)
        key = os.getenv("RESPAN_API_KEY") or os.getenv("RESPAN_GATEWAY_API_KEY")
        if not key:
            raise RuntimeError("RESPAN_API_KEY is required for explicit trace export")
        exporter = RespanSpanExporter(
            endpoint=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
            api_key=key,
        )
        original = exporter._session.post

        def post(url, *args, **kwargs):
            payload = (
                json.loads(kwargs["data"]) if kwargs.get("data") else kwargs.get("json")
            )
            response = original(url, *args, **kwargs)
            if os.getenv("RESPAN_EXAMPLE_WIRE_DIR"):
                _wire.append({"payload": payload, "http_status": response.status_code})
            return response

        exporter._session.post = post
        _provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(_provider)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    if _provider is None:
        return
    _provider.force_flush()
    spans = _memory.get_finished_spans()
    worker = os.getenv("PYTEST_XDIST_WORKER", "controller")
    scenario = os.environ["RESPAN_EXAMPLE_SCENARIO"]
    report = {
        "run_id": os.environ["RESPAN_EXAMPLE_RUN_ID"],
        "scenario": scenario,
        "worker": worker,
        "native_exit": int(exitstatus),
        "span_count": len(spans),
        "spans": [
            {
                "name": s.name,
                "trace_id": format(s.context.trace_id, "032x"),
                "span_id": format(s.context.span_id, "016x"),
                "parent_span_id": format(s.parent.span_id, "016x")
                if s.parent
                else None,
                "attributes": dict(s.attributes),
                "status": s.status.status_code.name,
                "status_description": s.status.description,
                "events": [
                    {"name": e.name, "attributes": dict(e.attributes)} for e in s.events
                ],
            }
            for s in spans
        ],
    }
    for variable, data in [
        ("RESPAN_EXAMPLE_REPORT_DIR", report),
        (
            "RESPAN_EXAMPLE_WIRE_DIR",
            {
                "run_id": report["run_id"],
                "scenario": scenario,
                "worker": worker,
                "entries": _wire,
            },
        ),
    ]:
        directory = os.getenv(variable)
        if directory:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            (path / f"{scenario}-{worker}.json").write_text(json.dumps(data, indent=2))
    print(f"local_spans={len(spans)} worker={worker}")
