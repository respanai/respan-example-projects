"""Dify async chat and workflow streams traced after consumption."""

from __future__ import annotations

import asyncio

from _shared import DifyExampleRuntime, parse_sse_line, print_result


async def run_async_examples(runtime: DifyExampleRuntime) -> dict[str, object]:
    try:
        from dify_client import AsyncChatClient, AsyncWorkflowClient
    except ImportError:
        return {
            "workflow": runtime.workflow_name,
            "status": "skipped",
            "reason": "installed dify-client does not expose async clients",
        }

    user = runtime.user("async")
    chat_parts: list[str] = []
    async with AsyncChatClient(
        runtime.api_key("DIFY_CHAT_API_KEY"),
        base_url=runtime.base_url,
    ) as chat_client:
        chat_response = await chat_client.create_chat_message(
            inputs={},
            query="Stream a concise async Dify response.",
            user=user,
            response_mode="streaming",
        )
        chat_response.raise_for_status()
        async for line in chat_response.aiter_lines():
            event = parse_sse_line(line)
            if event and event.get("answer"):
                chat_parts.append(str(event["answer"]))

    workflow_events: list[dict[str, object]] = []
    async with AsyncWorkflowClient(
        runtime.api_key("DIFY_WORKFLOW_API_KEY"),
        base_url=runtime.base_url,
    ) as workflow_client:
        workflow_response = await workflow_client.run(
            inputs={"query": "Run the async tracing workflow."},
            response_mode="streaming",
            user=user,
        )
        workflow_response.raise_for_status()
        async for line in workflow_response.aiter_lines():
            event = parse_sse_line(line)
            if event:
                workflow_events.append(event)

    return {
        "workflow": runtime.workflow_name,
        "status": "completed",
        "chat_answer": "".join(chat_parts),
        "workflow_events": [event.get("event") for event in workflow_events],
    }


def main() -> None:
    workflow_name = "dify_async_chat_and_workflow.workflow"
    with DifyExampleRuntime(workflow_name) as runtime:
        summary = asyncio.run(run_async_examples(runtime))
        runtime.set_result(summary)
        print_result("async_chat_and_workflow", summary)


if __name__ == "__main__":
    main()
