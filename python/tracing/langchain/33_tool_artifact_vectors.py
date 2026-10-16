"""Source tool IDs, full vector artifacts, and current calls distinct from history."""

from _shared import ToolCallingFakeMessagesListChatModel, init_telemetry, tracing_config
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool


@tool(response_format="content_and_artifact")
def vector_tool(label: str) -> tuple:
    """Return controlled full numeric vector."""
    return label, {
        "vector": [i / 5000 for i in range(5000)],
        "sparse_vector": {i * 2: i / 256 for i in range(256)},
    }


def main():
    init_telemetry("langchain-vector")
    calls = [
        {
            "name": "vector_tool",
            "args": {"label": label},
            "id": f"actual-vector-{label}",
        }
        for label in ("first", "second")
    ]
    model = ToolCallingFakeMessagesListChatModel(
        responses=[AIMessage(content="", tool_calls=calls)]
    )
    bound = model.bind_tools([vector_tool])
    answer = bound.invoke(
        [
            AIMessage(
                content="",
                tool_calls=[{"name": "prior", "args": {}, "id": "history-only"}],
            ),
            ToolMessage(content="old result", tool_call_id="history-only"),
            HumanMessage(content="Return two vectors"),
        ],
        config=tracing_config("vector_current_calls"),
    )
    for call in answer.tool_calls:
        result = vector_tool.invoke(call, config=tracing_config("vector_tool"))
        assert (
            len(result.artifact["vector"]) == 5000 and result.tool_call_id == call["id"]
        )
        assert len(result.artifact["sparse_vector"]) == 256
    print("Two actual calls and full vector artifacts preserved.")


if __name__ == "__main__":
    main()
