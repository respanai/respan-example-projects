"""Suppress agent/model/embedding content while retaining reported usage."""

from _shared import configure_respan, finish_respan, print_result
from openinference.instrumentation import TraceConfig


def run_private():
    respan = configure_respan(
        "haystack-content-opt-out",
        config=TraceConfig(hide_inputs=True, hide_outputs=True),
    )
    try:
        from haystack.components.agents import Agent
        from haystack.components.embedders import MockTextEmbedder
        from haystack.components.generators.chat import MockChatGenerator
        from haystack.dataclasses import ChatMessage

        agent = Agent(
            chat_generator=MockChatGenerator(
                responses="private haystack answer",
                meta={
                    "usage": {
                        "prompt_tokens": 5,
                        "completion_tokens": 3,
                        "total_tokens": 8,
                    }
                },
            )
        )
        assert (
            agent.run(messages=[ChatMessage.from_user("private haystack prompt")])[
                "last_message"
            ].text
            == "private haystack answer"
        )
        assert (
            len(
                MockTextEmbedder(dimension=128).run("private haystack embedding")[
                    "embedding"
                ]
            )
            == 128
        )
        print_result(
            "Content opt-out",
            {
                "agent_completed": True,
                "embedding_completed": True,
                "content_capture": False,
            },
        )
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run_private()
