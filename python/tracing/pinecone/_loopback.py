"""Deterministic protocol fixture used by the real Pinecone SDK examples."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import RLock, Thread
from typing import Any
from urllib.parse import parse_qs, urlsplit

_lock = RLock()
_server: ThreadingHTTPServer | None = None
_thread: Thread | None = None


class _Handler(BaseHTTPRequestHandler):
    server_version = "PineconeExampleFixture/1.0"

    def log_message(self, *_args: Any) -> None:
        return

    def _reply(self, status: int, value: object) -> None:
        payload = json.dumps(value, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def do_GET(self) -> None:
        if self.path.startswith("/indexes"):
            self._reply(200, {"indexes": []})
            return
        if self.path.startswith("/vectors/list"):
            result = {
                "vectors": [
                    {"id": "doc-2" if "paginationToken" in self.path else "doc-1"}
                ],
                "namespace": "demo",
            }
            if "paginationToken" not in self.path:
                result["pagination"] = {"next": "next-page"}
            self._reply(200, result)
            return
        if self.path.startswith("/namespaces"):
            self._reply(200, {"namespaces": [{"name": "demo", "recordCount": 1}]})
            return
        if self.path.startswith("/bulk/imports"):
            self._reply(
                200,
                {
                    "data": [
                        {
                            "id": "import-1",
                            "uri": "s3://fixture",
                            "status": "Completed",
                            "createdAt": "2026-10-03T00:00:00Z",
                        }
                    ]
                },
            )
            return
        if self.path.startswith("/vectors/fetch"):
            query = parse_qs(urlsplit(self.path).query)
            vector_id = (query.get("ids") or ["trace-doc"])[0]
            namespace = (query.get("namespace") or ["respan-example"])[0]
            self._reply(
                200,
                {
                    "namespace": namespace,
                    "vectors": {
                        vector_id: {
                            "id": vector_id,
                            "values": [1.0, 0.0, 0.0, 0.0],
                            "metadata": {"topic": "tracing"},
                        }
                    },
                },
            )
            return
        self._reply(404, {"message": "not found"})

    def do_POST(self) -> None:
        body = self._body()
        if self.path.endswith("/documents/upsert"):
            self._reply(200, {"upserted_count": len(body["documents"])})
        elif self.path.endswith("/documents/search"):
            self._reply(
                200,
                {
                    "namespace": "demo",
                    "matches": [{"_id": "doc-1", "_score": 0.99, "title": "tracing"}],
                    "usage": {"read_units": 1},
                },
            )
        elif self.path.endswith("/documents/fetch"):
            self._reply(
                200,
                {
                    "namespace": "demo",
                    "documents": {"doc-1": {"_id": "doc-1", "title": "tracing"}},
                    "usage": {"read_units": 1},
                },
            )
        elif self.path.endswith("/documents/update") or self.path.endswith(
            "/documents/delete"
        ):
            self._reply(200, {"matched_records": 1})
        elif self.path.endswith("/documents/list"):
            if body.get("pagination_token"):
                self._reply(
                    200,
                    {
                        "namespace": "demo",
                        "documents": [{"_id": "doc-2"}],
                        "usage": {"read_units": 1},
                    },
                )
            else:
                self._reply(
                    200,
                    {
                        "namespace": "demo",
                        "documents": [{"_id": "doc-1"}],
                        "usage": {"read_units": 1},
                        "pagination": {"next": "page-2"},
                    },
                )
        elif self.path == "/describe_index_stats":
            self._reply(
                200,
                {
                    "dimension": 4,
                    "indexFullness": 0.0,
                    "namespaces": {"respan-example": {"vectorCount": 3}},
                    "totalVectorCount": 3,
                },
            )
        elif self.path == "/vectors/upsert":
            self._reply(200, {"upsertedCount": len(body.get("vectors", []))})
        elif self.path == "/query":
            self._reply(
                200,
                {
                    "namespace": body.get("namespace", "respan-example"),
                    "matches": [
                        {
                            "id": "trace-doc",
                            "score": 0.99,
                            "values": [1.0, 0.0, 0.0, 0.0],
                            "metadata": {
                                "topic": "tracing",
                                "text": "Pinecone instrumentation is active.",
                            },
                        }
                    ],
                },
            )
        elif self.path == "/vectors/delete" and body.get("namespace") == "error":
            self._reply(503, {"message": "deterministic Pinecone outage"})
        elif self.path == "/vectors/delete":
            self._reply(200, {})
        else:
            self._reply(404, {"message": "not found"})


def loopback_host() -> str:
    global _server, _thread
    with _lock:
        if _server is None:
            _server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
            _thread = Thread(target=_server.serve_forever, daemon=True)
            _thread.start()
        host, port = _server.server_address
        return f"http://{host}:{port}"


def shutdown_loopback() -> None:
    global _server, _thread
    with _lock:
        server, thread = _server, _thread
        _server = None
        _thread = None
    if server is not None:
        server.shutdown()
        server.server_close()
    if thread is not None:
        thread.join(timeout=2)
