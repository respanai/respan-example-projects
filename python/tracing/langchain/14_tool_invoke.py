"""Tool invoke."""

from _shared import get_weather, init_telemetry, tracing_config


def tool_invoke() -> None:
    init_telemetry("langchain-tool-invoke")
    response = get_weather.invoke(
        {"city": "Tokyo"},
        config=tracing_config("tool_invoke"),
    )
    print(response)


if __name__ == "__main__":
    tool_invoke()
