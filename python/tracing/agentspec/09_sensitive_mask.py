"""Upstream sensitive-information masking includes callback-enriched prompts."""

from _fixtures import build_agent, fixture_model
from _shared import build_respan, example_scope, latest_message_content


def main():
    respan = build_respan("sensitive-mask", mask_sensitive_information=True)
    with example_scope("sensitive-mask"):
        try:
            with fixture_model():
                result = build_agent().invoke(
                    {"messages": [{"role": "user", "content": "private-mask-prompt"}]}
                )
            assert latest_message_content(result) == "answer private-mask-prompt"
            print({"masked_operations": 1})
        finally:
            respan.shutdown()


if __name__ == "__main__":
    main()
