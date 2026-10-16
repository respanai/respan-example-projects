"""Agent stream custom."""

from _shared import fake_tool_calling_model, init_telemetry, tracing_config
from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.config import get_stream_writer


@tool
def progress_weather(city: str) -> str:
    """Get deterministic weather and emit custom stream updates."""
    writer = get_stream_writer()
    writer({"stage": "lookup", "city": city})
    writer({"stage": "complete", "city": city})
    return f"It is sunny in {city}."


def agent_stream_custom() -> None:
    init_telemetry("langchain-agent-stream-custom")
    model = fake_tool_calling_model(
        tool_name="progress_weather",
        args={"city": "Denver"},
        final_text="Denver is sunny.",
    )
    agent = create_agent(model=model, tools=[progress_weather])
    chunks = list(
        agent.stream(
            {"messages": [{"role": "user", "content": "Weather in Denver?"}]},
            config=tracing_config("agent_stream_custom"),
            stream_mode="custom",
            version="v2",
        )
    )
    print(chunks)


if __name__ == "__main__":
    agent_stream_custom()
