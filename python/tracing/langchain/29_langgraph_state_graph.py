"""Native LangGraph compiled invoke/stream use LangChain callback managers."""

from typing import TypedDict

from _shared import init_telemetry, tracing_config
from langgraph.graph import StateGraph


class State(TypedDict):
    value: str


def main():
    init_telemetry("langchain-graph")
    graph = StateGraph(State)
    graph.add_node("echo", lambda state: {"value": state["value"] + "!"})
    graph.set_entry_point("echo")
    graph.set_finish_point("echo")
    app = graph.compile()
    assert app.invoke(
        {"value": "controlled"}, config=tracing_config("langgraph_state")
    ) == {"value": "controlled!"}
    assert list(
        app.stream({"value": "controlled"}, config=tracing_config("langgraph_stream"))
    )
    print("Graph invoke and stream passed.")


if __name__ == "__main__":
    main()
