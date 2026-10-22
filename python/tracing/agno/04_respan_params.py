"""Attach customer, thread, and metadata params to Agno spans."""

from _shared import build_agent, create_respan, example_attributes, print_result
from respan import workflow


@workflow(name="agno_04_respan_params")
def run_params_agent() -> str:
    agent = build_agent(
        name="Params Agent",
        instructions="Answer as a support assistant.",
    )
    result = agent.run("Summarize why tracing context matters.")
    return str(result.content)


def respan_params() -> None:
    respan, _ = create_respan(
        app_name="agno-04-respan-params",
        customer_identifier="user_12345",
        thread_identifier="thread_agno_demo",
        metadata={"plan": "premium", "example": "agno"},
    )

    try:
        with (
            example_attributes(respan, "agno_04_respan_params"),
            respan.propagate_attributes(
                custom_identifier="agno-run-001",
                metadata={"request_type": "demo"},
            ),
        ):
            output = run_params_agent()
    finally:
        respan.shutdown()

    print_result("Agent output", output)


if __name__ == "__main__":
    respan_params()
