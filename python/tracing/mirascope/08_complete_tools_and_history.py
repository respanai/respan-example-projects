"""Complete current/history call IDs, JSON schema and dense/sparse tool data."""

from __future__ import annotations

import json

from _controlled import Provider, model, vector_tool
from _shared import create_respan, finish_respan, workflow_attributes
from mirascope import llm
from respan import workflow


@workflow(name="mirascope-complete-tools-history")
def run():
    call = llm.ToolCall(
        id="complete-tool-" + "x" * 600,
        name="vector_tool",
        args=json.dumps(
            {"values": list(range(5000)), "api_key": "synthetic credential with spaces"}
        ),
    )
    native, _ = model(Provider(content=call))
    response = native.call(
        [llm.messages.user(str(i)) for i in range(150)], tools=[vector_tool]
    )
    output = response.execute_tools()[0]
    assert output.id == call.id and output.error is None
    assert (
        len(output.result["embedding"]) == len(output.result["sparse_vector"]) == 5000
    )
    native.call(response.messages)
    return {
        "history_messages": 150,
        "dense_values": 5000,
        "sparse_values": 5000,
        "call_id_length": len(call.id),
        "schema_sensitive_property": True,
    }


def main():
    runtime = create_respan("mirascope-complete-tools-history")
    try:
        with runtime.propagate_attributes(
            **workflow_attributes("mirascope-complete-tools-history", __file__)
        ):
            print(json.dumps(run()))
    finally:
        finish_respan(runtime)


if __name__ == "__main__":
    main()
