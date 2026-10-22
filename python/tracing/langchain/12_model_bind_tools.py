"""Chat model bind_tools."""

from _shared import fake_tool_calling_model, get_weather, init_telemetry, tracing_config


def model_bind_tools() -> None:
    init_telemetry("langchain-model-bind-tools")
    model = fake_tool_calling_model(
        tool_name="get_weather",
        args={"city": "Boston"},
        final_text="Boston is sunny.",
    )
    model_with_tools = model.bind_tools([get_weather])
    ai_message = model_with_tools.invoke(
        "What is the weather in Boston?",
        config=tracing_config("model_bind_tools"),
    )
    tool_messages = [
        get_weather.invoke(tool_call, config=tracing_config("model_bind_tools_tool"))
        for tool_call in ai_message.tool_calls
    ]
    print([message.content for message in tool_messages])


if __name__ == "__main__":
    model_bind_tools()
