"""Actual embedded LanceDB, local OTel by default, explicit export opt-in."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from uuid import uuid4

from opentelemetry import trace
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv_ai import SpanAttributes
from respan_instrumentation_lancedb import LanceDBInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA

RUN_ID = os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"lancedb-local-{uuid4().hex}"


def rows(n=20, dimension=4):
    return [
        {
            "id": i,
            "text": "native searchable row",
            "vector": [float(i)] * dimension,
            "flag": False,
            "zero": 0,
        }
        for i in range(n)
    ]


class Marker(SpanProcessor):
    def __init__(self, scenario):
        self.scenario = scenario

    def on_start(self, span, parent_context=None):
        values = {"run_id": RUN_ID, "scenario": self.scenario, "example_set": "lancedb"}
        span.set_attribute(RESPAN_METADATA, json.dumps(values))
        for key, value in values.items():
            span.set_attribute(f"{RESPAN_METADATA}.{key}", value)

    def on_end(self, span):
        pass


def run_scenario(name, function):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(Marker(name))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
        from dotenv import load_dotenv
        from respan_tracing.exporters.respan import RespanSpanExporter

        load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)
        key = os.getenv("RESPAN_API_KEY")
        if not key:
            raise RuntimeError("RESPAN_API_KEY is required for explicit export")
        provider.add_span_processor(
            SimpleSpanProcessor(
                RespanSpanExporter(
                    endpoint="https://api.respan.ai/api/v2/traces", api_key=key
                )
            )
        )
    trace.set_tracer_provider(provider)
    instrumentor = LanceDBInstrumentor()
    instrumentor.activate(tracer_provider=provider)
    try:
        with provider.get_tracer("lancedb.examples").start_as_current_span(
            name,
            attributes={
                RESPAN_LOG_TYPE: "workflow",
                SpanAttributes.TRACELOOP_ENTITY_NAME: name,
                SpanAttributes.TRACELOOP_ENTITY_PATH: "",
            },
        ):
            result = function()
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
        print(
            json.dumps(
                {
                    "scenario": name,
                    "result": result,
                    "spans": len(exporter.get_finished_spans()),
                }
            )
        )
    finally:
        instrumentor.deactivate()
        provider.force_flush()
        directory = os.getenv("RESPAN_EXAMPLE_REPORT_DIR")
        if directory:
            output = Path(directory)
            output.mkdir(parents=True, exist_ok=True)
            output.joinpath(f"{name}.json").write_text(
                json.dumps(
                    {
                        "run_id": RUN_ID,
                        "spans": [
                            json.loads(span.to_json())
                            for span in exporter.get_finished_spans()
                        ],
                    },
                    indent=2,
                )
            )
        provider.shutdown()
