"""Completion: call the LlamaIndex OpenAI LLM directly."""

from _shared import build_llm, create_respan, print_result, traced_example


def run_completion() -> None:
    context = create_respan(
        app_name="llama-index-01-completion",
        example_name="01_completion",
    )
    llm = build_llm(settings=context.settings)

    with traced_example(context):
        response = llm.complete(
            "Write one short sentence about what LlamaIndex query engines do."
        )

    print_result("Completion", response)
    print_result("Example run id", context.run_id)


if __name__ == "__main__":
    run_completion()
