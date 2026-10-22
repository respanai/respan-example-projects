"""Route Agno model calls through the Respan gateway."""

from _shared import build_agent, create_respan, example_attributes, print_result
from respan import workflow


@workflow(name="agno_02_gateway")
def run_gateway() -> str:
    agent = build_agent(
        name="Gateway Agent",
        instructions="Keep the answer short and concrete.",
    )
    result = agent.run("Name two practical uses for distributed tracing.")
    return str(result.content)


def gateway() -> None:
    respan, settings = create_respan(app_name="agno-02-gateway")
    try:
        with example_attributes(respan, "agno_02_gateway"):
            output = run_gateway()
    finally:
        respan.shutdown()
    print_result("Model", settings.model)
    print_result("Agent output", output)


if __name__ == "__main__":
    gateway()
