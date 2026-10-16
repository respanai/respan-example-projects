"""Complete source embedding and tool vectors, including controlled provider usage."""

from _fixtures import client_context
from _shared import (
    create_braintrust_logger,
    create_respan,
    flush_and_shutdown,
    new_run_id,
    workflow_context,
)

NAME = "05_full_embeddings"
WORKFLOW = "Braintrust Embeddings"


def main():
    marker = new_run_id(NAME)
    respan = create_respan(workflow_name=WORKFLOW, run_id=marker, example_name=NAME)
    logger = create_braintrust_logger(workflow_name=WORKFLOW)
    try:
        with (
            workflow_context(
                respan, workflow_name=WORKFLOW, run_id=marker, example_name=NAME
            ),
            logger.start_span(name=WORKFLOW, type="eval") as root,
        ):
            with client_context() as client:
                response = client.embeddings.create(
                    model="fixture-embed", input=["fixture"], encoding_format="float"
                )
            assert len(response.data[0].embedding) == 5000
            with root.start_span(name="vector_tool", type="tool") as tool:
                tool.log(
                    input={"value": 2},
                    output={"vector": [float(i) for i in range(5000)]},
                    metadata={"tool_call_id": "actual-vector-execution-id"},
                )
        print("Full 5000-dimensional provider/tool vectors verified")
    finally:
        flush_and_shutdown(respan, logger)


if __name__ == "__main__":
    main()
