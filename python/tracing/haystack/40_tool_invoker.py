"""Tool invocation through the native Agent executor (ToolInvoker on Haystack 2)."""

from _shared import configure_respan, create_tool_runner, finish_respan, print_result


def run_tool_invoker_example():
    respan = configure_respan("haystack-tool-invoker")
    try:
        from haystack.dataclasses import ChatMessage
        from haystack.dataclasses.chat_message import ToolCall
        from haystack.tools import Tool

        def add(a: int, b: int) -> str:
            return str(a + b)

        tool = Tool(
            name="add",
            description="Add two integers.",
            parameters={
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
            },
            function=add,
        )
        message = ChatMessage.from_assistant(
            tool_calls=[
                ToolCall(tool_name="add", arguments={"a": 19, "b": 23}, id="call_1")
            ]
        )
        result = create_tool_runner([tool]).run(messages=[message])
        print_result("Agent tool invocation", result)
        return result
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run_tool_invoker_example()
