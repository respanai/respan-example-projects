import inspect
import os
import threading
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

from _shared import create, points, run_scenario
from opentelemetry import context
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def scenario(provider, exporter):
    with closing(QdrantClient(":memory:")) as client:
        create(client)
        client.upsert("docs", points=points())
        before = len(exporter.get_finished_spans())
        token = context.attach(
            context.set_value(context._SUPPRESS_INSTRUMENTATION_KEY, True)
        )
        try:
            assert client.count("docs", exact=True).count == 3
        finally:
            context.detach(token)
        assert len(exporter.get_finished_spans()) == before
        provider.sampler.recording = False
        try:
            assert client.count("docs", exact=True).count == 3
        finally:
            provider.sampler.recording = True
        assert len(exporter.get_finished_spans()) == before
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        try:
            assert client.count("docs", exact=True).count == 3
        finally:
            context.detach(token)
        private = exporter.get_finished_spans()[-1]
        assert (
            "traceloop.entity.input" not in private.attributes
            and "traceloop.entity.output" not in private.attributes
        )
        assert not private.events and (not private.status.description)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            body = b'{"status":{"error":"controlled native HTTP missing collection"}}'
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        options = {"url": f"http://127.0.0.1:{server.server_port}"}
        if "check_compatibility" in inspect.signature(QdrantClient.__init__).parameters:
            options["check_compatibility"] = False
        with closing(QdrantClient(**options)) as client:
            try:
                client.get_collection("missing")
            except UnexpectedResponse as error:
                assert error.status_code == 404
            else:
                raise AssertionError("native HTTP404 required")
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
    live = "skipped: explicit live opt-in required"
    if os.getenv("RESPAN_EXAMPLE_LIVE") == "1":
        with closing(
            QdrantClient(
                url=os.environ["QDRANT_URL"], api_key=os.getenv("QDRANT_API_KEY")
            )
        ) as client:
            name = "respan_example_" + uuid4().hex[:12]
            create(client, name)
            try:
                client.upsert(name, points=points())
                assert client.count(name, exact=True).count == 3
                live = "native live roundtrip completed"
            finally:
                client.delete_collection(name)
    return {"native_http_error": 404, "private_native_count": 3, "optional_live": live}


if __name__ == "__main__":
    run_scenario("controls-http-live", scenario)
