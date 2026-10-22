"""Shared helpers for Dify tracing examples."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import uuid
from contextlib import AbstractContextManager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import TracebackType
from typing import Any, Self

from dotenv import load_dotenv
from opentelemetry.semconv_ai import SpanAttributes

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]
WORKSPACE_ROOT = REPO_ROOT.parent


def load_repo_env() -> None:
    load_dotenv(REPO_ROOT / ".env", override=False)
    load_dotenv(EXAMPLE_DIR / ".env", override=False)


class _LocalDifyHandler(BaseHTTPRequestHandler):
    server_version = "LocalDify/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0") or 0)
        return self.rfile.read(length) if length else b""

    def _json_body(self) -> dict[str, Any]:
        body = self._body()
        if not body:
            return {}
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _send_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def _send_sse(self, events: list[dict[str, Any]]) -> None:
        data = b"".join(f"data: {json.dumps(event)}\n\n".encode() for event in events)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    @staticmethod
    def _usage(prompt_tokens: int = 9, completion_tokens: int = 5) -> dict[str, Any]:
        return {
            "model": "dify/local-test-model",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "total_price": "0.0000000",
            "currency": "USD",
            "latency": 0.01,
        }

    def do_GET(self) -> None:
        if self.path.startswith("/datasets"):
            self._send_json(
                {
                    "data": [
                        {
                            "id": "dataset-local",
                            "name": "Local tracing knowledge base",
                        }
                    ],
                    "page": 1,
                    "limit": 20,
                    "total": 1,
                }
            )
            return
        if self.path.startswith("/workspaces/current/models/model-types/"):
            self._send_json(
                {
                    "data": [
                        {
                            "provider": "local",
                            "model": "dify/local-test-model",
                            "model_type": "llm",
                        }
                    ]
                }
            )
            return
        if self.path.startswith("/parameters"):
            self._send_json(
                {
                    "opening_statement": "Local Dify app ready.",
                    "user_input_form": [
                        {"text-input": {"label": "query", "variable": "query"}}
                    ],
                }
            )
            return
        if self.path.startswith("/conversations"):
            self._send_json(
                {
                    "data": [
                        {
                            "id": "conv-local-001",
                            "name": "Local conversation",
                            "inputs": {},
                            "status": "normal",
                        }
                    ],
                    "has_more": False,
                    "limit": 20,
                }
            )
            return
        if self.path.startswith("/messages"):
            self._send_json(
                {
                    "data": [
                        {
                            "id": "msg-local-001",
                            "conversation_id": "conv-local-001",
                            "query": "Hello",
                            "answer": "Hello from local Dify.",
                        }
                    ],
                    "has_more": False,
                    "limit": 20,
                }
            )
            return
        self._send_json({"error": f"Unhandled GET {self.path}"}, status=404)

    def do_POST(self) -> None:
        if self.path == "/files/upload":
            self._body()
            self._send_json(
                {
                    "id": "upload-local-001",
                    "name": "sample.txt",
                    "size": 24,
                    "extension": "txt",
                    "mime_type": "text/plain",
                }
            )
            return

        payload = self._json_body()
        response_mode = payload.get("response_mode", "blocking")
        user = payload.get("user", "local-user")

        if self.path == "/chat-messages":
            if response_mode == "streaming":
                self._send_sse(
                    [
                        {
                            "event": "message",
                            "task_id": "task-chat-stream",
                            "message_id": "msg-chat-stream",
                            "conversation_id": "conv-chat-stream",
                            "answer": "Streaming ",
                        },
                        {
                            "event": "message",
                            "task_id": "task-chat-stream",
                            "message_id": "msg-chat-stream",
                            "conversation_id": "conv-chat-stream",
                            "answer": "Dify response.",
                        },
                        {
                            "event": "message_end",
                            "task_id": "task-chat-stream",
                            "message_id": "msg-chat-stream",
                            "conversation_id": "conv-chat-stream",
                            "metadata": {"usage": self._usage(7, 4)},
                        },
                    ]
                )
                return
            self._send_json(
                {
                    "event": "message",
                    "task_id": "task-chat-blocking",
                    "message_id": "msg-chat-blocking",
                    "conversation_id": "conv-chat-blocking",
                    "mode": "chat",
                    "answer": f"Hello {user}. Dify chat tracing is active.",
                    "metadata": {"usage": self._usage(8, 6)},
                    "created_at": 1770000000,
                }
            )
            return

        if self.path == "/completion-messages":
            self._send_json(
                {
                    "event": "message",
                    "task_id": "task-completion",
                    "message_id": "msg-completion",
                    "mode": "completion",
                    "answer": "Dify completion tracing is active.",
                    "metadata": {"usage": self._usage(6, 5)},
                    "created_at": 1770000001,
                }
            )
            return

        if self.path == "/workflows/run":
            if response_mode == "streaming":
                self._send_sse(
                    [
                        {
                            "event": "workflow_started",
                            "task_id": "task-workflow",
                            "workflow_run_id": "workflow-run-local-001",
                        },
                        {
                            "event": "workflow_finished",
                            "task_id": "task-workflow",
                            "workflow_run_id": "workflow-run-local-001",
                            "data": {
                                "id": "workflow-run-local-001",
                                "workflow_id": "workflow-local",
                                "status": "succeeded",
                                "outputs": {"result": "Workflow stream finished."},
                                "total_tokens": 12,
                                "total_steps": 3,
                            },
                        },
                    ]
                )
                return
            self._send_json(
                {
                    "task_id": "task-workflow",
                    "workflow_run_id": "workflow-run-local-001",
                    "data": {
                        "id": "workflow-run-local-001",
                        "workflow_id": "workflow-local",
                        "status": "succeeded",
                        "outputs": {"result": "Workflow blocking result."},
                        "error": None,
                        "elapsed_time": 0.01,
                        "total_tokens": 12,
                        "total_steps": 3,
                    },
                }
            )
            return

        if self.path.endswith("/pipeline/run"):
            if response_mode == "streaming":
                self._send_sse(
                    [
                        {
                            "event": "workflow_started",
                            "task_id": "task-rag-pipeline",
                            "workflow_run_id": "rag-run-local-001",
                        },
                        {
                            "event": "workflow_finished",
                            "task_id": "task-rag-pipeline",
                            "workflow_run_id": "rag-run-local-001",
                            "data": {
                                "status": "succeeded",
                                "outputs": {"documents": 1},
                                "total_steps": 2,
                            },
                        },
                    ]
                )
                return
            self._send_json(
                {
                    "task_id": "task-rag-pipeline",
                    "workflow_run_id": "rag-run-local-001",
                    "data": {
                        "status": "succeeded",
                        "outputs": {"documents": 1},
                        "total_steps": 2,
                    },
                }
            )
            return

        if self.path.startswith("/messages/") and self.path.endswith("/feedbacks"):
            self._send_json({"result": "success"})
            return

        if self.path.startswith("/conversations/") and self.path.endswith("/name"):
            self._send_json({"result": "success", "name": payload.get("name")})
            return

        self._send_json({"error": f"Unhandled POST {self.path}"}, status=404)


class LocalDifyServer(AbstractContextManager):
    def __init__(self) -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _LocalDifyHandler)
        self.base_url = f"http://127.0.0.1:{self._server.server_port}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> Self:
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


class DifyExampleRuntime(AbstractContextManager):
    def __init__(self, workflow_name: str) -> None:
        self.workflow_name = workflow_name
        self.run_id = os.getenv("RESPAN_EXAMPLE_RUN_ID") or (
            f"dify-{workflow_name}-{uuid.uuid4().hex[:8]}"
        )
        self.respan = None
        self.base_url = ""
        self.is_local = False
        self._server_context: LocalDifyServer | None = None
        self._attributes_context = None
        self._workflow_context = None
        self._workflow_span = None
        self._result: Any = None

    def __enter__(self) -> Self:
        load_repo_env()
        self._configure_dify_endpoint()

        from respan import Respan, get_client
        from respan_instrumentation_dify import DifyInstrumentor

        self.respan = Respan(
            api_key=os.getenv("RESPAN_API_KEY"),
            base_url=os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api"),
            app_name=self.workflow_name,
            instrumentations=[DifyInstrumentor()],
            metadata={
                "integration": "dify",
                "run_id": self.run_id,
                "workflow_name": self.workflow_name,
            },
            is_batching_enabled=False,
            log_level=os.getenv("RESPAN_LOG_LEVEL", "WARNING"),
        )
        self._attributes_context = self.respan.propagate_attributes(
            custom_identifier=self.run_id,
            trace_group_identifier=self.workflow_name,
            metadata={
                "integration": "dify",
                "run_id": self.run_id,
                "workflow_name": self.workflow_name,
            },
        )
        self._attributes_context.__enter__()
        self._workflow_context = get_client().start_span(
            self.workflow_name,
            kind="workflow",
        )
        self._workflow_span = self._workflow_context.__enter__()
        if self._workflow_span is not None:
            self._workflow_span.set_attribute(
                SpanAttributes.TRACELOOP_ENTITY_INPUT,
                json.dumps({"scenario": self.workflow_name}, separators=(",", ":")),
            )
        print(f"example_run_id={self.run_id}")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            if self._workflow_span is not None:
                output = (
                    {"error": str(exc)}
                    if exc is not None
                    else self._result or {"status": "completed"}
                )
                self._workflow_span.set_attribute(
                    SpanAttributes.TRACELOOP_ENTITY_OUTPUT,
                    json.dumps(output, default=str, separators=(",", ":")),
                )
            if self._workflow_context is not None:
                self._workflow_context.__exit__(exc_type, exc, tb)
        finally:
            if self._attributes_context is not None:
                self._attributes_context.__exit__(exc_type, exc, tb)
            if self.respan is not None:
                self.respan.shutdown()
            if self._server_context is not None:
                self._server_context.__exit__(exc_type, exc, tb)

    def _configure_dify_endpoint(self) -> None:
        base_url = os.getenv("DIFY_BASE_URL")
        if base_url:
            self.base_url = base_url.rstrip("/")
            print(f"Using Dify endpoint: {self.base_url}")
            return

        self._server_context = LocalDifyServer().__enter__()
        self.base_url = self._server_context.base_url
        self.is_local = True
        print(f"Using local Dify-compatible test server: {self.base_url}")

    def api_key(self, kind: str = "DIFY_API_KEY") -> str:
        return os.getenv(kind) or os.getenv("DIFY_API_KEY") or "local-dify-key"

    def chat_client(self):
        from dify_client import ChatClient

        return self._sync_client(ChatClient, "DIFY_CHAT_API_KEY")

    def completion_client(self):
        from dify_client import CompletionClient

        return self._sync_client(CompletionClient, "DIFY_COMPLETION_API_KEY")

    def raw_client(self):
        from dify_client import DifyClient

        return self._sync_client(DifyClient, "DIFY_WORKFLOW_API_KEY")

    def workflow_client(self):
        try:
            from dify_client import WorkflowClient
        except ImportError:
            return None
        return self._sync_client(WorkflowClient, "DIFY_WORKFLOW_API_KEY")

    def knowledge_base_client(self, dataset_id: str):
        try:
            from dify_client import KnowledgeBaseClient
        except ImportError:
            return None
        api_key = self.api_key("DIFY_DATASET_API_KEY")
        return KnowledgeBaseClient(
            api_key=api_key,
            base_url=self.base_url,
            dataset_id=dataset_id,
        )

    def workspace_client(self):
        try:
            from dify_client import WorkspaceClient
        except ImportError:
            return None
        return self._sync_client(WorkspaceClient, "DIFY_DATASET_API_KEY")

    def _sync_client(self, client_class: Any, api_key_name: str):
        api_key = self.api_key(api_key_name)
        try:
            return client_class(api_key=api_key, base_url=self.base_url)
        except TypeError:
            # Released dify-client 0.1.10 accepts only api_key and reads the
            # mutable base_url property. The refreshed 0.1.12 source captures
            # base_url in an httpx client at construction time.
            client = client_class(api_key)
            client.base_url = self.base_url
            return client

    def user(self, suffix: str) -> str:
        return f"respan-dify-{suffix}-{uuid.uuid4().hex[:8]}"

    def set_result(self, value: Any) -> None:
        self._result = value


class sample_file(AbstractContextManager):
    def __enter__(self) -> Any:
        self._tmp = tempfile.NamedTemporaryFile("w+b", suffix=".txt", delete=False)
        self._tmp.write(b"Dify file upload tracing sample.\n")
        self._tmp.flush()
        self.path = Path(self._tmp.name)
        self._tmp.close()
        self.file = self.path.open("rb")
        return self.file

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.file.close()
        self.path.unlink(missing_ok=True)


def parse_sse_line(line: bytes | str) -> dict[str, Any] | None:
    text = line.decode("utf-8") if isinstance(line, bytes) else line
    text = text.strip()
    if not text:
        return None
    if text.startswith("data:"):
        text = text.split("data:", 1)[1].strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def collect_stream_answer(response: Any) -> str:
    parts: list[str] = []
    for line in response.iter_lines():
        event = parse_sse_line(line)
        if not event:
            continue
        answer = event.get("answer")
        if answer:
            parts.append(str(answer))
    return "".join(parts)


def print_result(label: str, value: Any) -> None:
    print(f"\n== {label} ==")
    print(json.dumps(value, indent=2, sort_keys=True, default=str))
