"""Actual Qdrant local engine, local OTel by default, explicit export opt-in."""

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
from opentelemetry.sdk.trace.sampling import ALWAYS_OFF, ALWAYS_ON, Sampler
from opentelemetry.semconv_ai import SpanAttributes
from respan_instrumentation_qdrant import QdrantInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA

RUN_ID = os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"qdrant-local-{uuid4().hex}"


class ExampleSampler(Sampler):
    """Use the real OTel sampler protocol for the explicit sampling scenario."""

    recording = True

    def should_sample(self, *args, **kwargs):
        native = ALWAYS_ON if self.recording else ALWAYS_OFF
        return native.should_sample(*args, **kwargs)

    def get_description(self):
        return "ExampleSampler"


class Marker(SpanProcessor):
    def __init__(self, scenario):
        self.scenario = scenario

    def on_start(self, span, parent_context=None):
        values = {
            "run_id": RUN_ID,
            "scenario": self.scenario,
            "example_set": "qdrant",
        }
        span.set_attribute(RESPAN_METADATA, json.dumps(values))
        for key, value in values.items():
            span.set_attribute(f"{RESPAN_METADATA}.{key}", value)

    def on_end(self, span):
        pass


def run_scenario(name, function):
    exporter = InMemorySpanExporter()
    provider = TracerProvider(sampler=ExampleSampler())
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
    instrumentor = QdrantInstrumentor(tracer_provider=provider)
    instrumentor.activate()
    try:
        with provider.get_tracer("qdrant.examples").start_as_current_span(
            name,
            attributes={
                RESPAN_LOG_TYPE: "workflow",
                SpanAttributes.TRACELOOP_ENTITY_NAME: name,
                SpanAttributes.TRACELOOP_ENTITY_PATH: "",
            },
        ):
            result = function(provider, exporter)
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


def points(count=3, dimension=4):
    from qdrant_client import models

    return [
        models.PointStruct(
            id=i,
            vector=[1.0] * dimension,
            payload={
                "text": f"native {i}",
                "flag": False,
                "zero": 0,
                "empty": "",
                "tag": "even" if i % 2 == 0 else "odd",
            },
        )
        for i in range(count)
    ]


def create(client, name="docs", dimension=4):
    from qdrant_client import models

    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(
            size=dimension, distance=models.Distance.DOT
        ),
    )


def query(client, name="docs", vector=None, limit=3, with_vectors=True):
    vector = [1.0] * 4 if vector is None else vector
    if callable(getattr(client, "query_points", None)):
        return client.query_points(
            collection_name=name, query=vector, limit=limit, with_vectors=with_vectors
        ).points
    return client.search(
        collection_name=name,
        query_vector=vector,
        limit=limit,
        with_vectors=with_vectors,
    )
