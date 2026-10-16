"""Agent invoke."""

from _shared import fake_tool_calling_model, get_weather, init_telemetry, tracing_config
from langchain.agents import create_agent


def agent_invoke() -> None:
    init_telemetry("langchain-agent-invoke")
    model = fake_tool_calling_model(
        tool_name="get_weather",
        args={"city": "San Francisco"},
        final_text="San Francisco is sunny.",
    )
    agent = create_agent(
        model=model,
        tools=[get_weather],
        system_prompt="Use tools when they help answer the user.",
    )
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "Weather in San Francisco?"}]},
        config=tracing_config("agent_invoke"),
    )
    print(response["messages"][-1].content)


if __name__ == "__main__":
    agent_invoke()
