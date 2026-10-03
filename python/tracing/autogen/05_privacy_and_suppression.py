"""Privacy survives iterator handoff; suppressed operations emit no logical spans."""

from _shared import client, response, run
from autogen_agentchat.agents import AssistantAgent
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


async def scenario():
    def private_tool() -> int:
        """Return a private fixture value."""
        return 0

    model = await client(
        response(calls=[("private-call", "private_tool", "{}")]),
        response("Suppressed fixture answer."),
        response("Visible fixture answer."),
    )
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        stream = AssistantAgent(
            "private_agent", model_client=model, tools=[private_tool]
        ).run_stream(task="Private fixture input.")
    finally:
        context.detach(token)
    result = [event async for event in stream][-1]
    assert result.messages[-1].content == "0"
    token = context.attach(
        context.set_value(context._SUPPRESS_INSTRUMENTATION_KEY, True)
    )
    try:
        await AssistantAgent("suppressed_agent", model_client=model).run(
            task="Suppressed fixture input."
        )
    finally:
        context.detach(token)
    visible = await AssistantAgent("visible_agent", model_client=model).run(
        task="Visible fixture input."
    )
    assert visible.messages[-1].content == "Visible fixture answer."
    return "Privacy and scoped suppression verified."


if __name__ == "__main__":
    run("privacy-and-suppression", scenario)
