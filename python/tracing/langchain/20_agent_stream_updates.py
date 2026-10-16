"""Agent stream updates."""

from _shared import fake_tool_calling_model, get_weather, init_telemetry, tracing_config
from langchain.agents import create_agent


def agent_stream_updates() -> None:
    init_telemetry("langchain-agent-stream-updates")
    model = fake_tool_calling_model(
        tool_name="get_weather",
        args={"city": "Austin"},
        final_text="Austin is sunny.",
    )
    agent = create_agent(model=model, tools=[get_weather])
    chunks = list(
        agent.stream(
            {"messages": [{"role": "user", "content": "Weather in Austin?"}]},
            config=tracing_config("agent_stream_updates"),
            stream_mode="updates",
            version="v2",
        )
    )
    print(chunks)


if __name__ == "__main__":
    agent_stream_updates()
