"""Actual native Milvus SDK and released Lite gRPC engine examples."""

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

import grpc
import pymilvus
from opentelemetry import context
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pymilvus import AnnSearchRequest, DataType, MilvusClient, RRFRanker
from respan_instrumentation_milvus import MilvusInstrumentor
from respan_sdk.constants.span_attributes import RESPAN_LOG_TYPE, RESPAN_METADATA
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

RUN_ID = os.getenv("RESPAN_EXAMPLE_RUN_ID") or "milvus-local-" + uuid4().hex
SCENARIOS = (
    "01_collection_lifecycle",
    "02_data_operations",
    "03_expected_error",
    "04_hybrid_search",
    "05_iterator_lifecycle",
    "06_async_client",
    "07_privacy_and_siblings",
    "08_native_task",
)


class Marker(SpanProcessor):
    def __init__(self, scenario):
        self.scenario = scenario

    def on_start(self, span, parent_context=None):
        data = {"run_id": RUN_ID, "scenario": self.scenario, "example_set": "milvus"}
        span.set_attribute(RESPAN_METADATA, json.dumps(data))
        for key, value in data.items():
            span.set_attribute(RESPAN_METADATA + "." + key, value)

    def on_end(self, span):
        pass


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


@contextmanager
def native_server():
    external = os.getenv("RESPAN_MILVUS_URI")
    if external:
        yield external
        return
    with tempfile.TemporaryDirectory(prefix="respan-milvus-") as directory:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        binary = os.getenv("RESPAN_MILVUS_LITE_EXECUTABLE") or str(
            Path(sys.executable).parent / "milvus-lite"
        )
        with (Path(directory) / "server.log").open("w") as log:
            process = subprocess.Popen(
                [
                    binary,
                    "server",
                    "--data-dir",
                    str(Path(directory) / "db"),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                stdout=log,
                stderr=log,
            )
            channel = grpc.insecure_channel(f"127.0.0.1:{port}")
            try:
                for _ in range(150):
                    if process.poll() is not None:
                        raise RuntimeError("Native Lite server exited")
                    try:
                        grpc.channel_ready_future(channel).result(timeout=0.1)
                        break
                    except grpc.FutureTimeoutError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError("Native Lite server unavailable")
                yield f"http://127.0.0.1:{port}"
            finally:
                channel.close()
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def populated(client, name="native_docs", count=3, dimension=4):
    schema = client.create_schema(auto_id=False, enable_dynamic_field=True)
    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=dimension)
    client.create_collection(name, schema=schema)
    rows = [
        {
            "id": i,
            "vector": [float(i % 3)] * dimension,
            "text": f"native row {i}",
            "flag": False,
        }
        for i in range(count)
    ]
    client.insert(name, rows)
    return name, rows


def run(scenario, function):
    provider = TracerProvider()
    memory = InMemorySpanExporter()
    wire = []
    statuses = []
    provider.add_span_processor(Marker(scenario))
    provider.add_span_processor(SimpleSpanProcessor(memory))
    if os.getenv("RESPAN_EXAMPLE_EXPORT") == "1":
        provider.add_span_processor(
            SimpleSpanProcessor(_remote_exporter(wire, statuses))
        )
    owner = MilvusInstrumentor(tracer_provider=provider)
    owner.activate()
    try:
        with (
            native_server() as uri,
            provider.get_tracer("milvus-examples").start_as_current_span(
                scenario, attributes={RESPAN_LOG_TYPE: "workflow"}
            ),
        ):
            client = MilvusClient(uri=uri)
            try:
                result = function(client, uri, provider)
            finally:
                client.close()
    finally:
        owner.deactivate()
        provider.force_flush()
    spans = [
        {
            "name": s.name,
            "trace_id": f"{s.context.trace_id:032x}",
            "span_id": f"{s.context.span_id:016x}",
            "parent_span_id": f"{s.parent.span_id:016x}" if s.parent else None,
            "attributes": dict(s.attributes),
            "status": s.status.status_code.name,
            "description": s.status.description,
            "events": [
                {"name": e.name, "attributes": dict(e.attributes)} for e in s.events
            ],
        }
        for s in memory.get_finished_spans()
    ]
    assert all(
        s["attributes"].get(RESPAN_METADATA + ".run_id") == RUN_ID for s in spans
    )
    for s in spans:
        if s["attributes"].get("db.system") == "milvus":
            assert (
                s["attributes"][RESPAN_LOG_TYPE] == "task"
                and "traceloop.span.kind" not in s["attributes"]
            )
            assert not any(k.startswith("gen_ai.") for k in s["attributes"])
    record = {
        "scenario": scenario,
        "run_id": RUN_ID,
        "result": result,
        "local": spans,
        "wire": wire,
        "statuses": statuses,
    }
    folder = os.getenv("RESPAN_EXAMPLE_EVIDENCE_DIR")
    if folder:
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
        (path / (scenario + ".json")).write_text(json.dumps(record))
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
    return record


def collection_lifecycle(client, _uri, _provider):
    name, _ = populated(client)
    assert client.has_collection(name) and name in client.list_collections()
    assert client.describe_collection(name)["collection_name"] == name
    client.drop_collection(name)
    return {"remaining": len(client.list_collections())}


def data_operations(client, _uri, _provider):
    name, rows = populated(client, count=75, dimension=5001)
    queried = client.query(
        name, filter="id>=0", limit=75, output_fields=["id", "vector", "text", "flag"]
    )
    assert len(queried) == 75 and len(queried[0]["vector"]) == 5001
    assert len(client.get(name, ids=[0], output_fields=["id", "vector"])) == 1
    client.upsert(name, rows[:1])
    client.delete(name, ids=[74])
    assert not client.get(name, ids=[74])
    return {"records": len(queried), "dimensions": len(queried[0]["vector"])}


def expected_error(client, _uri, _provider):
    try:
        client.query("absent", filter="id>=0")
    except pymilvus.exceptions.MilvusException:
        return {"native_error_preserved": True}
    raise AssertionError("Expected actual native error")


def hybrid_search(client, _uri, _provider):
    if not hasattr(MilvusClient, "hybrid_search"):
        return {"skipped": "Native2.4.1 lacks client hybrid_search"}
    name, _ = populated(client)
    indexes = client.prepare_index_params()
    indexes.add_index(field_name="vector", index_type="FLAT", metric_type="L2")
    client.create_index(name, indexes)
    client.load_collection(name)
    reqs = [
        AnnSearchRequest([[0.0] * 4], "vector", {"metric_type": "L2", "params": {}}, 2),
        AnnSearchRequest([[1.0] * 4], "vector", {"metric_type": "L2", "params": {}}, 2),
    ]
    result = client.hybrid_search(
        name, reqs, RRFRanker(), limit=2, output_fields=["id", "vector"]
    )
    assert len(result[0]) == 2
    return {"matches": len(result[0])}


def iterator_lifecycle(client, _uri, _provider):
    if not hasattr(MilvusClient, "query_iterator"):
        return {"skipped": "Native2.4.1 lacks client query_iterator"}
    name, _ = populated(client, count=5)
    iterator = client.query_iterator(
        name, batch_size=2, filter="id>=0", output_fields=["id", "vector"]
    )
    sizes = []
    try:
        while True:
            batch = iterator.next()
            sizes.append(len(batch))
            if not len(batch):
                break
    finally:
        iterator.close()
    assert sum(sizes) == 5
    return {"batch_sizes": sizes}


def async_client(client, uri, _provider):
    if not hasattr(pymilvus, "AsyncMilvusClient"):
        return {"skipped": "Native2.4.1 lacks async client"}
    name, _ = populated(client)

    async def call():
        async_client = pymilvus.AsyncMilvusClient(uri=uri)
        try:
            result = await async_client.query(
                name, filter="id>=0", output_fields=["id", "vector"]
            )
            assert len(result) == 3
            return {"records": len(result)}
        finally:
            await async_client.close()

    return asyncio.run(call())


def privacy_and_siblings(client, _uri, _provider):
    name, rows = populated(client)
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        client.upsert(name, [{**rows[0], "text": "PRIVATE"}])
        assert (
            client.query(name, filter="id==0", output_fields=["text"])[0]["text"]
            == "PRIVATE"
        )
    finally:
        context.detach(token)
    client.upsert(
        name, [{**rows[0], "text": 'Authorization: Bearer "CONTROLLED SPACE"'}]
    )
    carrier = context.get_current()

    def call():
        token = context.attach(carrier)
        try:
            return client.query(
                name, filter="id>=0", output_fields=["id", "vector", "text"]
            )
        finally:
            context.detach(token)

    with ThreadPoolExecutor(2) as pool:
        values = list(pool.map(lambda _: call(), range(2)))
    assert len(values) == 2
    return {"siblings": len(values)}


def native_task(client, _uri, _provider):
    if not hasattr(MilvusClient, "optimize"):
        return {"skipped": "Native2.4.1 lacks OptimizeTask"}
    name, _ = populated(client)
    task = client.optimize(name, target_size="invalid", wait=False)
    try:
        task.result(timeout=10)
    except pymilvus.exceptions.ParamError:
        return {"native_task_error_preserved": True}
    raise AssertionError("Expected actual native ParamError")
