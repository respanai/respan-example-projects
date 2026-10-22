"""TeamPipeline delegates a real local agent task and resumes its leader."""

import asyncio

from _shared import (
    ScriptedChatModel,
    build_respan,
    example_scope,
    text_response,
    tool_call_response,
)
from agentscope.agent import Agent
from agentscope.message import UserMsg
from agentscope.pipeline import TeamMember, TeamPipeline
from respan import workflow


async def main():
    leader_model = ScriptedChatModel(
        model="fixture-leader",
        responses=[
            tool_call_response(
                call_id="team-assignment",
                name="TeamAssign",
                arguments={"member": "Researcher", "prompt": "Summarize the fixture"},
            ),
            text_response("The team finished."),
        ],
    )
    member_model = ScriptedChatModel(
        model="fixture-researcher", responses=[text_response("Fixture summary ready.")]
    )
    leader = Agent(name="Leader", system_prompt="Delegate the task", model=leader_model)
    member = Agent(name="Researcher", system_prompt="Summarize", model=member_model)
    pipeline = TeamPipeline(
        leader=leader,
        members=[TeamMember(agent=member, description="Summarizes fixtures")],
    )
    respan = build_respan(
        "team-pipeline", "agentscope_team_pipeline", models=[leader_model, member_model]
    )

    @workflow(name="agentscope_team_pipeline")
    async def run(prompt):
        events = [
            event
            async for event in pipeline.reply_stream(
                UserMsg(name="user", content=prompt)
            )
        ]
        text = "".join(
            event.delta
            for event in events
            if str(event.type).lower() == "text_block_delta"
        )
        assert "Fixture summary ready." in text and "The team finished." in text
        return {"text": text, "events": len(events)}

    with example_scope("team-pipeline"):
        try:
            print(await run("Ask the researcher for a fixture summary"))
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
