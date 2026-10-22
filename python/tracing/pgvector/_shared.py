"""Genuine native PostgreSQL engine and OTel; export is explicitly optional."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from uuid import uuid4

from _native_engine import postgres
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv_ai import SpanAttributes
from respan_instrumentation_pgvector import PGVectorInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA

__all__ = [
    "Bit",
    "HalfVector",
    "SparseVector",
    "Vector",
    "run_scenario",
    "vector_values",
]

RUN_ID = os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"pgvector-local-{uuid4().hex}"


try:
    from pgvector import Bit, HalfVector, SparseVector, Vector
except ImportError:
    from pgvector.utils import Bit, HalfVector, SparseVector, Vector


def vector_values(value):
    return (
        value.to_list()
        if type(value) is Vector or type(value) is HalfVector
        else value.tolist()
    )


def seed(dsn):
    import pgvector.psycopg as native
    import psycopg

    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute("CREATE EXTENSION vector")
        native.register_vector(connection)
        connection.execute(
            "CREATE TABLE items(id integer,embedding vector(5001),payload jsonb,flag boolean,zero integer,empty text)"
        )
        payload = {
            "history": [{"position": i} for i in range(75)],
            "properties": {
                "api_key": {"type": "string", "default": "controlled-schema-secret"}
            },
            "password": "controlled-row-secret",
        }
        with connection.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO items VALUES (%s,%s,%s,%s,%s,%s)",
                [
                    (
                        i,
                        Vector([0.0] * 5001),
                        psycopg.types.json.Jsonb(payload),
                        False,
                        0,
                        "",
                    )
                    for i in range(75)
                ],
            )


class Marker(SpanProcessor):
    def __init__(self, scenario):
        self.scenario = scenario

    def on_start(self, span, parent_context=None):
        values = {
            "run_id": RUN_ID,
            "scenario": self.scenario,
            "example_set": "pgvector",
        }
        span.set_attribute(RESPAN_METADATA, json.dumps(values))
        for key, item in values.items():
            span.set_attribute(f"{RESPAN_METADATA}.{key}", item)


def append(path, value):
    if path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a") as output:
            output.write(json.dumps(value) + "\n")


def _run_scenario(name, function, dsn, *, capture_content=True):
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(Marker(name))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
        from dotenv import load_dotenv
        from respan_tracing.exporters.respan import RespanSpanExporter

        load_dotenv(
            os.getenv("RESPAN_EXAMPLE_ENV_FILE")
            or Path(__file__).resolve().parents[3] / ".env",
            override=False,
        )
        key = os.getenv("RESPAN_API_KEY") or os.getenv("RESPAN_GATEWAY_API_KEY")
        if not key:
            raise RuntimeError("RESPAN_API_KEY is required for explicit trace export")
        remote = RespanSpanExporter(
            endpoint=os.getenv(
                "RESPAN_TRACE_ENDPOINT", "https://api.respan.ai/api/v2/traces"
            ),
            api_key=key,
        )
        post = remote._session.post

        def observed(*args, **kwargs):
            response = post(*args, **kwargs)
            raw = kwargs.get("json", kwargs.get("data"))
            payload = json.loads(raw) if type(raw) in (str, bytes) else raw
            append(
                os.getenv("RESPAN_EXAMPLE_WIRE_PATH"),
                {"payload": payload, "http_status": response.status_code},
            )
            return response

        remote._session.post = observed
        provider.add_span_processor(SimpleSpanProcessor(remote))
    owner = PGVectorInstrumentor(
        tracer_provider=provider, capture_content=capture_content
    )
    owner.activate()
    try:
        with provider.get_tracer("pgvector.examples").start_as_current_span(
            name,
            attributes={
                RESPAN_LOG_TYPE: "workflow",
                SpanAttributes.TRACELOOP_ENTITY_NAME: name,
                SpanAttributes.TRACELOOP_ENTITY_PATH: "",
            },
        ):
            result = function(dsn)
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
        provider.force_flush()
        spans = exporter.get_finished_spans()
        for span in spans:
            append(
                os.getenv("RESPAN_EXAMPLE_LOCAL_PATH"),
                {
                    "trace_id": f"{span.context.trace_id:032x}",
                    "span_id": f"{span.context.span_id:016x}",
                    "parent_id": f"{span.parent.span_id:016x}" if span.parent else None,
                    "name": span.name,
                    "attributes": dict(span.attributes),
                    "status": span.status.status_code.name,
                    "status_description": span.status.description,
                    "events": [
                        {"name": e.name, "attributes": dict(e.attributes)}
                        for e in span.events
                    ],
                },
            )
        print(json.dumps({"scenario": name, "result": result, "spans": len(spans)}))
    finally:
        owner.deactivate()
        provider.shutdown()


def run_scenario(name, function, *, capture_content=True):
    with postgres() as dsn:
        seed(dsn)
        _run_scenario(name, function, dsn, capture_content=capture_content)
