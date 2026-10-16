"""A basic AgentSpec request handled by a deterministic local model."""

from _fixtures import build_agent, fixture_model
from _shared import build_respan, example_scope, latest_message_content


def main():
    respan = build_respan("basic-agent")
    with example_scope("basic-agent"):
        try:
            with fixture_model():
                result = build_agent("Poet").invoke(
                    {"messages": [{"role": "user", "content": "Write a fixture haiku"}]}
                )
            assert latest_message_content(result) == "answer Write a fixture haiku"
            print(latest_message_content(result))
        finally:
            respan.shutdown()


if __name__ == "__main__":
    main()
