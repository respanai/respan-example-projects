"""Agent stream messages."""

from _shared import fake_tool_calling_model, get_weather, init_telemetry, tracing_config
from langchain.agents import create_agent


def agent_stream_messages() -> None:
    init_telemetry("langchain-agent-stream-messages")
    model = fake_tool_calling_model(
        tool_name="get_weather",
        args={"city": "Seattle"},
        final_text="Seattle is sunny.",
    )
    agent = create_agent(model=model, tools=[get_weather])
    chunks = list(
        agent.stream(
            {"messages": [{"role": "user", "content": "Weather in Seattle?"}]},
            config=tracing_config("agent_stream_messages"),
            stream_mode="messages",
            version="v2",
        )
    )
    print(chunks)


if __name__ == "__main__":
    agent_stream_messages()
