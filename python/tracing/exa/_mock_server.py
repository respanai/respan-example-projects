from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse


class _Handler(BaseHTTPRequestHandler):
    server_version = "RespanExaMock/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _sse(self, chunks: list[dict[str, Any]]) -> None:
        body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks)
        body += "data: [DONE]\n\n"
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        body = self._body()
        if body.get("query") == "expected Exa provider error":
            self._json(429, {"error": "deterministic Exa rate limit"})
            return
        if path == "/search":
            if body.get("stream"):
                self._sse(
                    [
                        {"choices": [{"delta": {"content": "loopback "}}]},
                        {
                            "choices": [{"delta": {"content": "search"}}],
                            "citations": [
                                {
                                    "id": "source-1",
                                    "url": "https://example.com/search",
                                    "title": "Loopback source",
                                }
                            ],
                        },
                    ]
                )
                return
            self._json(
                200,
                {
                    "results": [
                        {
                            "id": "https://example.com/search",
                            "url": "https://example.com/search",
                            "title": "Loopback search result",
                            "text": "Deterministic Exa search content.",
                            "highlights": ["Deterministic Exa search content."],
                        }
                    ],
                    "requestId": "loopback-search-request",
                    "resolvedSearchType": body.get("type", "auto"),
                    "costDollars": {"total": 0.007, "search": {"neural": 0.007}},
                },
            )
            return
        if path == "/contents":
            urls = body.get("urls") or []
            self._json(
                200,
                {
                    "results": [
                        {
                            "id": url,
                            "url": url,
                            "title": "Loopback page",
                            "text": "Deterministic page contents for instrumentation.",
                            "highlights": ["Deterministic page contents."],
                        }
                        for url in urls
                    ],
                    "requestId": "loopback-contents-request",
                    "costDollars": {"total": 0.001, "contents": {"text": 0.001}},
                },
            )
            return
        if path == "/answer":
            if body.get("stream"):
                self._sse(
                    [
                        {"choices": [{"delta": {"content": "loopback "}}]},
                        {
                            "choices": [{"delta": {"content": "answer"}}],
                            "citations": [
                                {
                                    "id": "answer-source",
                                    "url": "https://example.com/answer",
                                    "title": "Answer source",
                                }
                            ],
                        },
                    ]
                )
                return
            self._json(
                200,
                {
                    "answer": "A deterministic grounded answer.",
                    "citations": [
                        {
                            "id": "answer-source",
                            "url": "https://example.com/answer",
                            "title": "Answer source",
                        }
                    ],
                    "costDollars": {"total": 0.005},
                },
            )
            return
        if path == "/agent/runs":
            if self.headers.get("accept") == "text/event-stream":
                events = [
                    {
                        "id": "event-1",
                        "event": "run.started",
                        "data": {"id": "run-loopback"},
                    },
                    {
                        "id": "event-2",
                        "event": "run.completed",
                        "data": {
                            "id": "run-loopback",
                            "output": {"text": "agent result"},
                        },
                    },
                ]
                encoded = "".join(
                    f"event: {event['event']}\ndata: {json.dumps(event)}\n\n"
                    for event in events
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("content-type", "text/event-stream")
                self.send_header("content-length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
                return
            self._json(
                200,
                {
                    "id": "run-loopback",
                    "object": "agent.run",
                    "status": "queued",
                    "request": body,
                },
            )
            return
        if path == "/research/v1":
            self._json(
                200,
                {
                    "researchId": "research-loopback",
                    "createdAt": time.time() * 1000,
                    "model": body.get("model", "exa-research-fast"),
                    "instructions": body.get("instructions", "loopback research"),
                    "status": "pending",
                },
            )
            return
        self._json(404, {"error": f"Unhandled POST {path}"})

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/agent/runs/run-loopback":
            self._json(
                200,
                {
                    "id": "run-loopback",
                    "object": "agent.run",
                    "status": "completed",
                    "output": {"text": "Deterministic agent result."},
                    "usage": {"agentComputeUnits": 1.0, "searches": 1},
                    "costDollars": {
                        "total": 0.012,
                        "agentCompute": 0.005,
                        "search": 0.007,
                    },
                },
            )
            return
        if path == "/research/v1/research-loopback":
            now = time.time() * 1000
            self._json(
                200,
                {
                    "researchId": "research-loopback",
                    "createdAt": now,
                    "model": "exa-research-fast",
                    "instructions": "Create a deterministic research brief.",
                    "status": "completed",
                    "output": {"content": "Deterministic legacy research output."},
                    "costDollars": {
                        "total": 0.02,
                        "numPages": 1,
                        "numSearches": 1,
                        "reasoningTokens": 32,
                    },
                },
            )
            return
        self._json(404, {"error": f"Unhandled GET {path}"})


@contextmanager
def run_mock_exa_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
