from __future__ import annotations

import json

from _shared import (
    example_attributes,
    example_run_id,
    finish_respan,
    make_respan,
    print_result,
    tracer,
    workflow,
    workflow_name,
)

EXAMPLE_NAME = "chat-provider"


@workflow(name=workflow_name(EXAMPLE_NAME))
def chat_provider_workflow(prompt: str) -> str:
    response = "OpenInference attributes are translated into one canonical contract."
    with tracer().start_as_current_span("openai.chat") as span:
        span.set_attribute("openinference.span.kind", "LLM")
        span.set_attribute("llm.model_name", "gpt-4.1-mini")
        span.set_attribute("llm.system", "OpenAI")
        span.set_attribute("llm.provider", "OpenAI")
        span.set_attribute("llm.invocation_parameters", '{"temperature":0.1}')
        span.set_attribute("llm.input_messages.0.message.role", "user")
        span.set_attribute("llm.input_messages.0.message.content", prompt)
        span.set_attribute("llm.output_messages.0.message.role", "assistant")
        span.set_attribute("llm.output_messages.0.message.content", response)
        span.set_attribute("llm.output_messages.0.message.finish_reason", "stop")
        span.set_attribute("llm.token_count.prompt", 11)
        span.set_attribute("llm.token_count.completion", 9)
        span.set_attribute("llm.token_count.total", 20)
        span.set_attribute("input.value", json.dumps({"prompt": prompt}))
        span.set_attribute("output.value", json.dumps({"response": response}))
    return response


def run() -> None:
    run_id = example_run_id()
    respan = make_respan(EXAMPLE_NAME, run_id)
    result = ""
    try:
        with example_attributes(EXAMPLE_NAME, run_id):
            result = chat_provider_workflow(
                "Explain the OpenInference translation boundary in one sentence."
            )
    finally:
        finish_respan(respan)
    print_result(EXAMPLE_NAME, run_id, result)


if __name__ == "__main__":
    run()
