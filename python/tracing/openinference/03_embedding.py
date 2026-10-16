from __future__ import annotations

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

EXAMPLE_NAME = "embedding"


@workflow(name=workflow_name(EXAMPLE_NAME))
def embedding_workflow(text: str) -> str:
    vector = tuple(i / 10000 for i in range(5000))
    with tracer().start_as_current_span("openai.embedding") as span:
        span.set_attribute("openinference.span.kind", "EMBEDDING")
        span.set_attribute("embedding.model_name", "text-embedding-3-small")
        span.set_attribute("embedding.embeddings.0.embedding.text", text)
        span.set_attribute("embedding.embeddings.0.embedding.vector", vector)
        span.set_attribute("llm.system", "openai")
        span.set_attribute("llm.provider", "openai")
        span.set_attribute("llm.token_count.prompt", 5)
        span.set_attribute("llm.token_count.total", 5)
    return f"captured deterministic vector with {len(vector)} dimensions"


def run() -> None:
    run_id = example_run_id()
    respan = make_respan(EXAMPLE_NAME, run_id)
    result = ""
    try:
        with example_attributes(EXAMPLE_NAME, run_id):
            result = embedding_workflow("OpenInference embedding contract")
    finally:
        finish_respan(respan)
    print_result(EXAMPLE_NAME, run_id, result)


if __name__ == "__main__":
    run()
