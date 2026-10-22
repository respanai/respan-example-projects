"""Parse a real LlamaIndex structured prediction from controlled provider data."""

from _shared import build_llm, create_respan, print_result, traced_example
from llama_index.core import PromptTemplate
from pydantic import BaseModel


class TraceTip(BaseModel):
    title: str
    action: str


def main() -> None:
    context = create_respan(
        app_name="llama-index-structured", example_name="09_structured_output"
    )
    llm = build_llm(context.settings)
    with traced_example(
        context,
        root_span_name=context.example_name,
        input_data={"request": "structured tracing tip"},
    ) as root:
        result = llm.structured_predict(
            TraceTip,
            PromptTemplate("Return a tracing tip about {topic}."),
            topic="errors",
        )
        assert result.title
        root.set_output(result.model_dump())
    print_result("Structured output", result.model_dump())


if __name__ == "__main__":
    main()
