"""Local native Chroma examples; remote Respan export is explicit."""

from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import chromadb
import httpx
from chromadb.config import Settings
from opentelemetry import context
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from respan_instrumentation_chroma import ChromaInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

RUN_ID = os.getenv("RESPAN_EXAMPLE_RUN_ID") or "chroma-local-" + uuid4().hex
SCENARIOS = (
    "01_collection_lifecycle",
    "02_write_and_read",
    "03_query_and_filters",
    "04_update_upsert_delete",
    "05_propagated_attributes",
    "06_async_http",
    "07_privacy_and_errors",
    "08_pending_siblings",
)


class Marker(SpanProcessor):
    def __init__(self, scenario):
        self.scenario = scenario

    def on_start(self, span, parent_context=None):
        data = {"run_id": RUN_ID, "scenario": self.scenario, "example_set": "chroma"}
        span.set_attribute(RESPAN_METADATA, json.dumps(data))
        for key, value in data.items():
            span.set_attribute(RESPAN_METADATA + "." + key, value)

    def on_end(self, span):
        pass


class DeterministicEmbeddingFunction:
    """No model downloads or provider requests."""

    @staticmethod
    def name():
        return "controlled-local"

    def __call__(self, input):
        return [[float(sum(map(ord, text)) % 23), 1.0, 2.0, 3.0] for text in input]

    def embed_query(self, input):
        return self(input)

    def embed_documents(self, input):
        return self(input)


def records(count=3, dimension=4):
    return {
        "ids": [f"doc-{i}" for i in range(count)],
        "documents": [f"Controlled native document {i}" for i in range(count)],
        "metadatas": [
            {"rank": i, "flag": False, "topic": "native"} for i in range(count)
        ],
        "embeddings": [[float(i % 3)] * dimension for i in range(count)],
    }


def collection(client, name="controlled_docs", *, count=3, dimension=4):
    col = client.create_collection(name, embedding_function=None)
    col.add(**records(count, dimension))
    return col


def _remote_exporter(wire, statuses):
    from dotenv import load_dotenv
    from respan_tracing.exporters.respan import RespanSpanExporter

    load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)
    key = os.environ["RESPAN_API_KEY"]
    exporter = RespanSpanExporter(
        endpoint="https://api.respan.ai/api/v2/traces", api_key=key
    )
    original = exporter._session.post

    def post(*args, **kwargs):
        # Observe the actual released exporter body; never retain headers.
        wire.append(json.loads(kwargs["data"]))
        response = original(*args, **kwargs)
        statuses.append(response.status_code)
        return response

    exporter._session.post = post
    return exporter


def run(scenario, function):
    provider = TracerProvider()
    memory = InMemorySpanExporter()
    wire, statuses = [], []
    provider.add_span_processor(Marker(scenario))
    provider.add_span_processor(SimpleSpanProcessor(memory))
    if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
        provider.add_span_processor(
            SimpleSpanProcessor(_remote_exporter(wire, statuses))
        )
    owner = ChromaInstrumentor(tracer_provider=provider)
    owner.activate()
    with tempfile.TemporaryDirectory(prefix="respan-chroma-") as directory:
        client = chromadb.PersistentClient(
            path=directory,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
        try:
            with provider.get_tracer("chroma-examples").start_as_current_span(
                scenario, attributes={RESPAN_LOG_TYPE: "workflow"}
            ):
                result = function(client, provider)
        finally:
            if hasattr(client, "close"):
                client.close()
            else:
                client._system.stop()
            owner.deactivate()
            provider.force_flush()
    spans = [
        {
            "name": span.name,
            "trace_id": f"{span.context.trace_id:032x}",
            "span_id": f"{span.context.span_id:016x}",
            "parent_span_id": f"{span.parent.span_id:016x}" if span.parent else None,
            "attributes": dict(span.attributes),
            "status": span.status.status_code.name,
            "description": span.status.description,
            "events": [
                {"name": event.name, "attributes": dict(event.attributes)}
                for event in span.events
            ],
        }
        for span in memory.get_finished_spans()
    ]
    assert all(RESPAN_METADATA + ".run_id" in span["attributes"] for span in spans)
    assert all("traceloop.span.kind" not in span["attributes"] for span in spans)
    for span in spans:
        if span["attributes"].get("db.system") == "chroma":
            assert span["attributes"][RESPAN_LOG_TYPE] == "task"
            assert not any(key.startswith("gen_ai.") for key in span["attributes"])
    evidence = {
        "scenario": scenario,
        "run_id": RUN_ID,
        "result": result,
        "local": spans,
        "wire": wire,
        "statuses": statuses,
    }
    location = os.getenv("RESPAN_EXAMPLE_EVIDENCE_DIR")
    if location:
        path = Path(location)
        path.mkdir(parents=True, exist_ok=True)
        (path / (scenario + ".json")).write_text(json.dumps(evidence))
    provider.shutdown()
    print(
        json.dumps(
            {
                "scenario": scenario,
                "spans": len(spans),
                "result": result,
                "http_statuses": statuses,
            }
        )
    )
    return evidence


def lifecycle(client, _provider):
    col = client.create_collection(
        "native_lifecycle", metadata={"flag": False, "zero": 0}, embedding_function=None
    )
    assert client.get_collection(col.name, embedding_function=None).id == col.id
    assert (
        client.get_or_create_collection(col.name, embedding_function=None).id == col.id
    )
    listed = client.list_collections(limit=0, offset=0)
    assert listed == [] and client.count_collections() == 1
    assert type(client.heartbeat()) is int
    client.delete_collection(col.name)
    return {"remaining": client.count_collections()}


def write_and_read(client, _provider):
    col = collection(client, count=75, dimension=5001)
    data = col.get(include=["embeddings", "documents", "metadatas"])
    assert len(data["ids"]) == 75 and len(data["embeddings"][0]) == 5001
    assert col.count() == 75 and len(col.peek(limit=1)["ids"]) == 1
    return {
        "records": len(data["ids"]),
        "vector_dimensions": len(data["embeddings"][0]),
    }


def query_and_filters(client, _provider):
    col = client.create_collection(
        "native_callback", embedding_function=DeterministicEmbeddingFunction()
    )
    rows = records()
    col.add(ids=rows["ids"], documents=rows["documents"], metadatas=rows["metadatas"])
    query = col.query(
        query_texts=["Controlled native document 0"],
        n_results=2,
        where={"flag": False},
        where_document={"$contains": "native"},
        include=["documents", "metadatas", "distances", "embeddings"],
    )
    assert len(query["ids"][0]) == 2
    return {"matches": len(query["ids"][0])}


def update_upsert_delete(client, _provider):
    col = collection(client)
    assert (
        col.update(ids=["doc-0"], documents=["changed"], embeddings=[[0.0] * 4]) is None
    )
    assert (
        col.upsert(ids=["new"], documents=["new native"], embeddings=[[1.0] * 4])
        is None
    )
    deleted = col.delete(ids=["doc-1"])
    col.modify(metadata={"flag": False, "zero": 0, "note": ""})
    assert col.count() == 3
    return {"remaining": col.count(), "native_delete_result": deleted}


def propagated_attributes(client, _provider):
    col = collection(client)
    col.get(where={"rank": {"$gte": 0}}, limit=0, offset=0, include=["documents"])
    if hasattr(col, "get_indexing_status"):
        try:
            status = col.get_indexing_status()
        except NotImplementedError:
            return {"native_indexing_status": "unsupported by the local engine"}
        assert status is not None
        return {"native_indexing_status": True}
    return {"native_indexing_status": "unavailable in Chroma 0.5"}


@contextmanager
def native_server():
    with tempfile.TemporaryDirectory(prefix="respan-chroma-http-") as path:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        with (Path(path) / "server.log").open("w") as log:
            process = subprocess.Popen(
                [
                    str(Path(sys.executable).parent / "chroma"),
                    "run",
                    "--path",
                    str(Path(path) / "db"),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                env=dict(os.environ, ANONYMIZED_TELEMETRY="False"),
                stdout=log,
                stderr=log,
            )
            try:
                for _ in range(150):
                    if process.poll() is not None:
                        raise RuntimeError("Native Chroma server exited")
                    try:
                        if (
                            httpx.get(
                                f"http://127.0.0.1:{port}/api/v2/heartbeat", timeout=1
                            ).status_code
                            == 200
                        ):
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.1)
                else:
                    raise RuntimeError("Native Chroma server did not start")
                yield port
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def async_http(_client, _provider):
    if not hasattr(chromadb, "AsyncHttpClient"):
        return {"skipped": "Native Chroma 0.5 has no AsyncHttpClient"}

    async def operations(port):
        client = await chromadb.AsyncHttpClient(
            host="127.0.0.1", port=port, settings=Settings(anonymized_telemetry=False)
        )
        col = await client.create_collection("native_async", embedding_function=None)
        await col.add(ids=["a"], documents=["native HTTP"], embeddings=[[0.0, 1.0]])
        output = await col.query(
            query_embeddings=[[0.0, 1.0]],
            n_results=1,
            include=["embeddings", "documents"],
        )
        assert output["ids"] == [["a"]]
        await client.delete_collection("native_async")
        return {"matches": len(output["ids"][0])}

    with native_server() as port:
        return asyncio.run(operations(port))


def privacy_and_errors(client, _provider):
    col = client.create_collection("native_privacy", embedding_function=None)
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        assert (
            col.add(ids=["a"], documents=["PRIVATE"], embeddings=[[0.0, 1.0]]) is None
        )
        assert col.get()["documents"] == ["PRIVATE"]
    finally:
        context.detach(token)
    col.update(
        ids=["a"],
        documents=['Authorization: Bearer "CONTROLLED SPACE"'],
        embeddings=[[0.0, 1.0]],
    )
    assert col.get()["documents"] == ['Authorization: Bearer "CONTROLLED SPACE"']
    try:
        col.add(ids=["duplicate", "duplicate"], embeddings=[[0.0, 1.0]] * 2)
    except chromadb.errors.DuplicateIDError:
        return {"native_error_preserved": True}
    raise AssertionError("Expected native DuplicateIDError")


def pending_siblings(client, provider):
    col = collection(client)
    carrier = context.get_current()

    def get():
        token = context.attach(carrier)
        try:
            return col.get(include=["embeddings"])
        finally:
            context.detach(token)

    with ThreadPoolExecutor(2) as pool:
        values = list(pool.map(lambda _: get(), range(2)))
    assert len(values) == 2
    return {"siblings": len(values)}
