"""User-defined Flow success, method parentage, and a controlled failure."""

from _fixtures import FixtureServer
from _shared import create_respan, run_with_attributes, shutdown_respan
from crewai.flow.flow import Flow, listen, start
from respan import workflow


class FixtureFlow(Flow):
    @start()
    def ask(self):
        return FixtureServer().llm().call("Answer the flow fixture.")

    @listen(ask)
    def finish(self, answer):
        return {"answer": answer}


class FailureFlow(Flow):
    @start()
    def fail(self):
        raise ValueError("controlled flow failure")


@workflow(name="crewai_06_flows")
def run_flows(scenario: str) -> dict:
    result = FixtureFlow().kickoff()
    try:
        FailureFlow().kickoff()
    except ValueError as exc:
        assert str(exc) == "controlled flow failure"
    return {"scenario": scenario, "result": result, "controlled_failure": True}


def main():
    context = create_respan(
        app_name="crewai-06-flows",
        example_name="06_flows",
        workflow_name="crewai_06_flows",
    )
    try:
        print(run_with_attributes(context, lambda: run_flows("flow-lifecycle")))
    finally:
        shutdown_respan(context)


if __name__ == "__main__":
    main()
