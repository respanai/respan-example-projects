"""ADK SSE events and early close preserve caller context."""

from _shared import (
    APP_USER_ID,
    DeterministicLlm,
    make_runner,
    make_user_message,
    run_scenario,
)
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode


async def scenario():
    runner, session = await make_runner(
        Agent(name="stream_agent", model=DeterministicLlm(model="fixture-adk"))
    )
    kwargs = {
        "user_id": APP_USER_ID,
        "session_id": session.id,
        "new_message": make_user_message("Synthetic streaming request"),
        "run_config": RunConfig(streaming_mode=StreamingMode.SSE),
    }
    complete = [event async for event in runner.run_async(**kwargs)]
    partial = runner.run_async(**kwargs)
    await anext(partial)
    await partial.aclose()
    return {"complete_events": len(complete), "early_closed": True}


if __name__ == "__main__":
    run_scenario("04_streaming", scenario)
