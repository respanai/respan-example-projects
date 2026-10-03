"""A real AgentSpec tool call with a zero-valued result and follow-up model."""

from _fixtures import build_agent, fixture_model
from _shared import build_respan, example_scope, latest_message_content


def main():
    respan = build_respan("tool-agent")
    with example_scope("tool-agent"):
        try:
            with fixture_model():
                result = build_agent("Calculator", with_tool=True).invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": "tool-call subtract equal values",
                            }
                        ]
                    }
                )
            assert latest_message_content(result) == "0.0"
            print({"tool_result": latest_message_content(result)})
        finally:
            respan.shutdown()


if __name__ == "__main__":
    main()
