"""Keep model and embedding content out of spans while retaining usage."""

from _gateway import finish_respan, make_respan
from pydantic_ai import Agent, Embedder
from pydantic_ai.embeddings.test import TestEmbeddingModel
from pydantic_ai.models.test import TestModel
from respan import workflow


@workflow(name="pydantic_ai_content_opt_out")
def run_private():
    result = Agent(
        TestModel(custom_output_text="private fixture answer"), name="private_agent"
    ).run_sync("private fixture prompt")
    assert result.output == "private fixture answer"
    result = Embedder(TestEmbeddingModel()).embed_query_sync("private embedding input")
    assert len(result.embeddings) == 1
    return {
        "content_capture": False,
        "agent_completed": True,
        "embedding_completed": True,
    }


def main():
    respan = None
    try:
        respan = make_respan(
            "content-opt-out", include_content=False, include_binary_content=False
        )
        print(run_private())
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
