"""Multi-agent message flow and deterministic failure traced by Respan."""

from __future__ import annotations

import asyncio

from _shared import (
    FailingChatModel,
    ScriptedChatModel,
    build_respan,
    example_scope,
    text_response,
)
from agentscope.agent import Agent
from agentscope.message import UserMsg


async def main() -> None:
    writer_model = ScriptedChatModel(
        model="agentscope-scripted-writer",
        responses=[text_response("Draft: tracing helps debug agent steps.")],
    )
    reviewer_model = ScriptedChatModel(
        model="agentscope-scripted-reviewer",
        responses=[text_response("Review: concise and accurate.")],
    )
    failing_model = FailingChatModel(model="agentscope-scripted-failure", responses=[])
    respan = build_respan(
        example_name="multi-agent-and-failure",
        workflow_name="agentscope_multi_agent_and_failure",
        models=[writer_model, reviewer_model, failing_model],
    )

    with example_scope("multi-agent-and-failure"):
        try:
            writer = Agent(
                name="WriterAgent",
                system_prompt="Write one-sentence drafts.",
                model=writer_model,
            )
            reviewer = Agent(
                name="ReviewerAgent",
                system_prompt="Review the latest observed draft.",
                model=reviewer_model,
            )

            draft = await writer.reply(
                UserMsg(name="user", content="Write a tracing note.")
            )
            await reviewer.observe(draft)
            review = await reviewer.reply(
                UserMsg(name="user", content="Review the draft.")
            )
            assert draft.get_text_content().startswith("Draft:")
            assert review.get_text_content().startswith("Review:")
            print(draft.get_text_content())
            print(review.get_text_content())

            failing_agent = Agent(
                name="FailingAgent",
                system_prompt="Always fails for instrumentation coverage.",
                model=failing_model,
            )
            try:
                await failing_agent.reply(
                    UserMsg(name="user", content="Trigger failure.")
                )
            except RuntimeError as exc:
                assert str(exc) == "deterministic AgentScope model failure"
                print(f"Caught expected failure: {exc}")
            else:
                raise AssertionError("Expected controlled failure")
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
