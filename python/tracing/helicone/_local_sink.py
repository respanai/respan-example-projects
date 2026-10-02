"""Deterministic local receiver for HeliconeManualLogger examples."""

from __future__ import annotations

import atexit
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from typing import Any

_server: ThreadingHTTPServer | None = None
_thread: Thread | None = None
_requests: list[dict[str, Any]] = []
_lock = Lock()


class _Handler(BaseHTTPRequestHandler):
    server_version = "HeliconeExampleSink/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:
        content_length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = {"invalid": True}
        with _lock:
            _requests.append({"path": self.path, "body": payload})
        response = b'{"ok":true}'
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


def endpoint() -> str:
    global _server, _thread
    if _server is None:
        _server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        _thread = Thread(target=_server.serve_forever, daemon=True)
        _thread.start()
        atexit.register(shutdown)
    host, port = _server.server_address
    return f"http://{host}:{port}"


def reset() -> None:
    with _lock:
        _requests.clear()


def received() -> list[dict[str, Any]]:
    with _lock:
        return list(_requests)


def shutdown() -> None:
    global _server, _thread
    if _server is not None:
        _server.shutdown()
        _server.server_close()
    if _thread is not None:
        _thread.join(timeout=1)
    _server = None
    _thread = None
    reset()
