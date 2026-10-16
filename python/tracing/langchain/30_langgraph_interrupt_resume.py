"""Public dynamic interrupt, checkpoint, and resume on current LangGraph."""

from typing import TypedDict

from _shared import init_telemetry, tracing_config
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    value: str


def node(state):
    return {"value": interrupt("Approve controlled value?")}


def main():
    init_telemetry("langchain-interrupt")
    graph = StateGraph(State)
    graph.add_node("confirm", node)
    graph.set_entry_point("confirm")
    graph.set_finish_point("confirm")
    app = graph.compile(checkpointer=MemorySaver())
    cfg = {
        **tracing_config("langgraph_interrupt"),
        "configurable": {"thread_id": "controlled-thread"},
    }
    assert "__interrupt__" in app.invoke({"value": "pending"}, config=cfg)
    assert app.invoke(Command(resume="approved"), config=cfg) == {"value": "approved"}
    print("Interrupt/resume preserved native control flow.")


if __name__ == "__main__":
    main()
