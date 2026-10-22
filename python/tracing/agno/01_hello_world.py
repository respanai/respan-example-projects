"""Bare-minimum Agno agent run with Respan tracing."""

from _shared import build_agent, create_respan, example_attributes, print_result
from respan import workflow


@workflow(name="agno_01_hello_world")
def run_hello_world() -> str:
    agent = build_agent(
        name="Hello Agent",
        instructions="Answer in one concise sentence.",
    )
    result = agent.run("What is Agno?")
    return str(result.content)


def hello_world() -> None:
    respan, _ = create_respan(app_name="agno-01-hello-world")
    try:
        with example_attributes(respan, "agno_01_hello_world"):
            output = run_hello_world()
    finally:
        respan.shutdown()
    print_result("Agent output", output)


if __name__ == "__main__":
    hello_world()
