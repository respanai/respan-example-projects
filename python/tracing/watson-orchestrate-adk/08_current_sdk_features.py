"""Current SDK paths using real methods and local HTTP/WebSocket fixtures."""

import asyncio

from _shared import (
    create_respan,
    deterministic_chat_client,
    deterministic_run_client,
    deterministic_watson_runtime,
    example_attributes,
    marker_for,
    workflow_name,
)
from ibm_watsonx_orchestrate_clients.ai_builder.agent_builder_client import (
    AgentBuilderClient,
)
from ibm_watsonx_orchestrate_clients.ai_builder.cpe.cpe_client import CPEClient
from ibm_watsonx_orchestrate_clients.tools.tempus_client import TempusClient
from respan import workflow

EXAMPLE_NAME = "current-sdk-features"


@workflow(name=workflow_name(EXAMPLE_NAME))
async def current_features(question: str) -> dict:
    run = deterministic_run_client()
    run.create_run_with_files(
        "",
        [
            {
                "filename": "fixture.txt",
                "url": "https://storage.invalid/file?signature=fixture-secret",
            }
        ],
        agent_id="fixture-agent",
    )
    run.wait_for_run_completion("fixture-run", poll_interval=0, max_retries=1)
    run.wait_for_run_completion("failed-run", poll_interval=0, max_retries=1)
    messages = []
    failed = await run.stream_run_with_websocket(
        "fixture-agent", "fixture-thread", "failed-run", on_message=messages.append
    )
    assert failed["status"] == "failed" and len(messages) == 1
    for kind in ("watsonx", "groq", "gateway"):
        response = deterministic_chat_client(kind).generate_response(
            question, instructions="Use the fixture lookup tool."
        )
        assert (
            response["choices"][0]["message"]["tool_calls"][0]["id"]
            == "call-fixture-lookup"
        )
    zero = deterministic_chat_client().generate_response("zero usage")
    assert zero["usage"]["total_tokens"] == 0
    architect = object.__new__(AgentBuilderClient)
    architect.chat_id = "fixture-chat"
    architect.submit_chat("architect-model", "Create a support agent.")
    cpe = object.__new__(CPEClient)
    cpe.chat_id = "fixture-cpe-chat"
    cpe.submit_chat_with_agent_architect("architect-model", "Create an agent.")
    cpe.submit_refine_agent_with_chats(
        "Use concise responses.",
        "architect-model",
        {},
        {},
        {},
        [],
        model="target-agent-model",
    )
    flow = object.__new__(TempusClient)
    flow.run_flow("fixture-flow", {"ticket_id": "INC-1001"})
    flow.arun_flow("fixture-flow-async", {"ticket_id": "INC-1002"})
    return {
        "status": "completed",
        "callbacks": len(messages),
        "failed_run_observed": True,
    }


async def main():
    marker = marker_for(EXAMPLE_NAME)
    with deterministic_watson_runtime():
        respan = create_respan(EXAMPLE_NAME, marker)
        try:
            with example_attributes(EXAMPLE_NAME, marker):
                result = await current_features("tool only")
        finally:
            respan.shutdown()
    print({"example": EXAMPLE_NAME, "marker": marker, "result": result}, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
