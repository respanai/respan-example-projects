"""One-script example for Respan prompt management with Haystack.

Set ``RESPAN_PROMPT_ID`` and either ``RESPAN_PROMPT_VARIABLES_JSON`` or the
``RESPAN_PROMPT_QUESTION`` / ``RESPAN_PROMPT_CONTEXT`` fallback variables before
running this script. The Respan gateway resolves the managed prompt and fills
the variables at request time, while ``propagate_attributes`` links the exported
Haystack trace back to the prompt.
"""

import json
import os

from _shared import configure_respan, finish_respan, print_result
from dotenv import find_dotenv, load_dotenv


def _prompt_variables() -> dict:
    variables_json = os.getenv("RESPAN_PROMPT_VARIABLES_JSON")
    if variables_json:
        try:
            variables = json.loads(variables_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "RESPAN_PROMPT_VARIABLES_JSON must be valid JSON."
            ) from exc
        if not isinstance(variables, dict):
            raise RuntimeError("RESPAN_PROMPT_VARIABLES_JSON must decode to an object.")
        return variables

    return {
        "question": os.getenv("RESPAN_PROMPT_QUESTION", "Who created Python?"),
        "context": os.getenv(
            "RESPAN_PROMPT_CONTEXT",
            "Python was created by Guido van Rossum and first released in 1991.",
        ),
    }


def _haystack_required_message(prompt_variables: dict) -> str:
    for key in ("customer_inquiry", "question", "user_query"):
        value = prompt_variables.get(key)
        if isinstance(value, str) and value:
            return value
    return "Run the managed Respan prompt."


def run_prompt_management_gateway_example():
    load_dotenv(find_dotenv(), override=False)

    prompt_id = os.getenv("RESPAN_PROMPT_ID")
    if not prompt_id:
        raise RuntimeError(
            "Set RESPAN_PROMPT_ID to a deployed Respan prompt before running "
            "the prompt management example."
        )

    prompt_variables = _prompt_variables()

    respan = configure_respan("haystack-prompt-management-gateway", use_gateway=True)
    try:
        from haystack import Pipeline
        from haystack.components.generators.chat import OpenAIChatGenerator
        from haystack.dataclasses import ChatMessage

        pipeline = Pipeline()
        pipeline.add_component(
            "managed_prompt_llm",
            OpenAIChatGenerator(model=os.getenv("RESPAN_MODEL", "gpt-4o-mini")),
        )

        with respan.propagate_attributes(
            prompt={"prompt_id": prompt_id, "variables": prompt_variables}
        ):
            result = pipeline.run(
                {
                    "managed_prompt_llm": {
                        # Haystack skips the OpenAI call when messages is empty.
                        # The gateway still resolves the managed prompt from
                        # extra_body.prompt and overrides these messages.
                        "messages": [
                            ChatMessage.from_user(
                                _haystack_required_message(prompt_variables)
                            )
                        ],
                        "generation_kwargs": {
                            "temperature": 0.0,
                            "extra_body": {
                                "prompt": {
                                    "prompt_id": prompt_id,
                                    "variables": prompt_variables,
                                    "override": True,
                                },
                            },
                        },
                    }
                }
            )

        print_result("Respan prompt management gateway", result)
        return result
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run_prompt_management_gateway_example()
