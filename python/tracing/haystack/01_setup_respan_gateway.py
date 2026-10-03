"""Gateway setup for Haystack OpenAIChatGenerator through Respan."""

import os

from _shared import configure_respan, finish_respan, print_result


def run_setup_respan_gateway_example():
    respan = configure_respan("haystack-setup-gateway", use_gateway=True)
    try:
        from haystack import Pipeline
        from haystack.components.builders import ChatPromptBuilder
        from haystack.components.generators.chat import OpenAIChatGenerator
        from haystack.dataclasses import ChatMessage

        pipeline = Pipeline()
        pipeline.add_component(
            "prompt_builder",
            ChatPromptBuilder(
                template=[ChatMessage.from_user("Answer concisely: {{ question }}")],
                required_variables=["question"],
            ),
        )
        pipeline.add_component(
            "llm",
            OpenAIChatGenerator(model=os.getenv("RESPAN_MODEL", "gpt-4o-mini")),
        )
        pipeline.connect("prompt_builder", "llm")

        result = pipeline.run(
            {"prompt_builder": {"question": "What is the capital of France?"}}
        )
        print_result("Gateway result", result)
        return result
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run_setup_respan_gateway_example()
