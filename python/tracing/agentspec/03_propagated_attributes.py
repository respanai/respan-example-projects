"""Propagated thread metadata and separate sequential-agent payloads."""

from _fixtures import build_agent, fixture_model
from _shared import build_respan, example_scope, latest_message_content, run_id


def main():
    respan = build_respan("propagated-attributes")
    with example_scope(
        "propagated-attributes", thread_identifier=run_id() + ":conversation"
    ):
        try:
            with fixture_model():
                outputs = [
                    latest_message_content(
                        build_agent("Agent-" + prompt).invoke(
                            {"messages": [{"role": "user", "content": prompt}]}
                        )
                    )
                    for prompt in ["first", "second"]
                ]
            assert outputs == ["answer first", "answer second"]
            print(outputs)
        finally:
            respan.shutdown()


if __name__ == "__main__":
    main()
