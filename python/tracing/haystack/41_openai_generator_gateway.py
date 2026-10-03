"""One-script example for OpenAIChatGenerator through the Respan gateway."""

import os

from _shared import configure_respan, finish_respan, print_result


def run_openai_generator_gateway_example():
    respan = configure_respan("haystack-openai-generator-gateway", use_gateway=True)
    try:
        from haystack.components.generators.chat import OpenAIChatGenerator
        from haystack.dataclasses import ChatMessage

        generator = OpenAIChatGenerator(model=os.getenv("RESPAN_MODEL", "gpt-4o-mini"))
        result = generator.run(
            messages=[
                ChatMessage.from_user(
                    "Answer in one sentence: what is retrieval augmented generation?"
                )
            ],
            generation_kwargs={"temperature": 0.0},
        )
        print_result("OpenAIChatGenerator gateway", result)
        return result
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run_openai_generator_gateway_example()
