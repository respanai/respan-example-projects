"""Shared helpers for Watson Orchestrate ADK Respan examples."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from dotenv import load_dotenv
from ibm_watsonx_orchestrate.client.autodiscover.watsonx_ai.watsonx_ai_client import (
    WatsonxAIClient,
)
from ibm_watsonx_orchestrate_clients.chat.run_client import RunClient
from respan import Respan, propagate_attributes
from respan_instrumentation_watson_orchestrate_adk import (
    WatsonOrchestrateADKInstrumentor,
)

EXAMPLE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EXAMPLE_DIR.parents[2]
DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai/api"
DEFAULT_MODEL = "watsonx/meta-llama/llama-3-3-70b-instruct"


class DeterministicWatsonError(Exception):
    status_code = 429


def load_repo_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def require_env(name: str) -> str:
    load_repo_env()
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set")
    return value


def optional_env(name: str) -> str | None:
    load_repo_env()
    return os.getenv(name) or None


def marker_for(example_name: str) -> str:
    return os.getenv("RESPAN_EXAMPLE_RUN_ID") or (
        f"watson-orchestrate-{example_name}-{uuid4().hex[:8]}"
    )


def workflow_name(example_name: str) -> str:
    return f"watson_orchestrate_{example_name.replace('-', '_')}"


def create_respan(app_name: str, marker: str) -> Respan:
    return Respan(
        app_name="watson-orchestrate-adk-examples",
        api_key=require_env("RESPAN_API_KEY"),
        base_url=os.getenv("RESPAN_BASE_URL", DEFAULT_RESPAN_BASE_URL),
        instrumentations=[WatsonOrchestrateADKInstrumentor()],
        is_batching_enabled=False,
        metadata={
            "integration": "watson-orchestrate-adk",
            "example": app_name,
            "run_id": marker,
            "example_run_id": marker,
        },
        environment="examples",
    )


@contextmanager
def example_attributes(example_name: str, marker: str) -> Iterator[None]:
    name = workflow_name(example_name)
    with propagate_attributes(
        custom_identifier=marker,
        trace_group_identifier=name,
        customer_identifier="watson-orchestrate-example-user",
        thread_identifier=f"{marker}-{example_name}",
        metadata={
            "example": example_name,
            "example_set": "watson-orchestrate-adk",
            "run_id": marker,
            "example_run_id": marker,
            "workflow_name": name,
        },
    ):
        yield


def _fixture_post(self, path, data):
    """Fixture only the transport; the installed SDK constructs every request."""
    messages = data.get("messages", [])
    prompt = (
        messages[-1].get("content", "")
        if messages
        else data.get("message", {}).get("content", "")
    )
    if isinstance(prompt, list):
        prompt = " ".join(
            part.get("text", "") for part in prompt if isinstance(part, dict)
        )
    if "provider failure" in prompt.lower():
        raise DeterministicWatsonError("deterministic provider rate limit")
    if "/flows/" in path:
        return {"run_id": "fixture-flow", "status": "queued", "input": data}
    if "/runs" in path:
        return {
            "run_id": "watson-run-deterministic",
            "thread_id": data.get("thread_id", "watson-thread-deterministic"),
            "status": "queued",
            "message": data["message"]["content"],
        }
    message = {
        "role": "assistant",
        "content": "Watson Orchestrate tracing is deterministic.",
    }
    if "tool only" in prompt.lower():
        message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-fixture-lookup",
                    "type": "function",
                    "function": {
                        "name": "lookup_ticket",
                        "arguments": '{"ticket_id":"INC-1001"}',
                    },
                }
            ],
        }
    return {
        "model": data.get("model", data.get("model_id", DEFAULT_MODEL)),
        "choices": [
            {
                "message": message,
                "finish_reason": "tool_calls" if "tool_calls" in message else "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0 if "zero usage" in prompt else 10,
            "completion_tokens": 0 if "zero usage" in prompt else 6,
            "total_tokens": 0 if "zero usage" in prompt else 16,
        },
    }


def _fixture_get(self, path):
    return {
        "run_id": path.rsplit("/", 1)[-1],
        "status": "failed" if "failed" in path else "completed",
        "error": "controlled run failure" if "failed" in path else None,
    }


def _fixture_nd_json(self, path, data):
    if "/agent/architect/" in path:
        return [
            {
                "event": "message.created",
                "data": {
                    "thread_id": "architect-thread",
                    "message": {
                        "role": "assistant",
                        "content": "Architect fixture response.",
                        "additional_properties": {"architect_conversational_state": {}},
                    },
                },
            }
        ]
    return [
        {"formatted_message": {"role": "assistant", "content": "CPE fixture response."}}
    ]


class _FixtureSocket:
    def __init__(self, **kwargs):
        self.handlers = {}
        self.failed = False

    def register_handler(self, name, callback):
        self.handlers[name] = callback

    async def connect(self, agent_id, thread_id, run_id):
        self.failed = "failed" in run_id

    async def listen(self):
        self.handlers["message.created"](
            {"event": "message.created", "data": {"message": "fixture message"}}
        )
        event = "run.failed" if self.failed else "run.completed"
        self.handlers[event](
            {
                "event": event,
                "data": {
                    "run_id": "watson-run-deterministic",
                    "status": "failed" if self.failed else "completed",
                    "error": "controlled failure" if self.failed else None,
                },
            }
        )

    async def disconnect(self):
        pass


@contextmanager
def deterministic_watson_runtime() -> Iterator[None]:
    from ibm_watsonx_orchestrate.client.autodiscover.ai_gateway.ai_gateway_client import (
        AIGatewayClient,
    )
    from ibm_watsonx_orchestrate.client.autodiscover.groq.groq_client import GroqClient
    from ibm_watsonx_orchestrate_clients.ai_builder.agent_builder_client import (
        AgentBuilderClient,
    )
    from ibm_watsonx_orchestrate_clients.ai_builder.cpe.cpe_client import CPEClient
    from ibm_watsonx_orchestrate_clients.chat import run_client
    from ibm_watsonx_orchestrate_clients.tools.tempus_client import TempusClient

    with ExitStack() as stack:
        for cls in (
            RunClient,
            WatsonxAIClient,
            GroqClient,
            AIGatewayClient,
            TempusClient,
        ):
            stack.enter_context(patch.object(cls, "_post", _fixture_post))
        stack.enter_context(patch.object(RunClient, "_get", _fixture_get))
        for cls in (AgentBuilderClient, CPEClient):
            stack.enter_context(patch.object(cls, "_post_nd_json", _fixture_nd_json))
        stack.enter_context(patch.object(run_client, "WebSocketClient", _FixtureSocket))
        yield


def deterministic_run_client() -> RunClient:
    client = object.__new__(RunClient)
    client.base_endpoint = "/runs"
    client.base_url = "https://watson.invalid/v1"
    client.api_key = "fixture-key"
    client.authenticator = None
    client.verify = True
    return client


def deterministic_chat_client(kind="watsonx") -> WatsonxAIClient:
    from ibm_watsonx_orchestrate.client.autodiscover.ai_gateway.ai_gateway_client import (
        AIGatewayClient,
    )
    from ibm_watsonx_orchestrate.client.autodiscover.groq.groq_client import GroqClient

    cls = {"watsonx": WatsonxAIClient, "groq": GroqClient, "gateway": AIGatewayClient}[
        kind
    ]
    client = object.__new__(cls)
    client.model = DEFAULT_MODEL if kind == "watsonx" else "fixture-model"
    client.space_id = "fixture-space"
    return client
