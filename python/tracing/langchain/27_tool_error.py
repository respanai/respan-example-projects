"""Tool error."""

from _shared import init_telemetry, tracing_config
from langchain_core.tools import tool


@tool
def failing_lookup(query: str) -> str:
    """Always fail to demonstrate tool error callbacks."""
    raise ValueError(f"no result for {query}")


def tool_error() -> None:
    init_telemetry("langchain-tool-error")
    try:
        failing_lookup.invoke(
            {"query": "missing"},
            config=tracing_config("tool_error"),
        )
    except ValueError as exc:
        print(f"caught: {exc}")


if __name__ == "__main__":
    tool_error()
