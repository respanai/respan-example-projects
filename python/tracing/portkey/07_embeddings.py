from _shared import (
    example_attributes,
    execution_id,
    finish_respan,
    make_client,
    make_respan,
    marker,
    print_result,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "embeddings"


@workflow(name=workflow_name(EXAMPLE_NAME))
def trace_embedding(values: list[str]):
    client = make_client()
    try:
        result = client.embeddings.create(model="fixture-embedding", input=values)
        assert len(result.data[0].embedding) == 3072
        return {
            "dimensions": len(result.data[0].embedding),
            "actual_prompt_tokens": result.usage.prompt_tokens,
        }
    finally:
        client.close()


def main():
    run = marker()
    respan = make_respan(EXAMPLE_NAME, run)
    try:
        with example_attributes(EXAMPLE_NAME, run, execution_id(), mode="fixture"):
            print_result(EXAMPLE_NAME, run, trace_embedding(["hello", "world"]))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
