"""A caught AgentOps task failure traced as a failed child span."""

from __future__ import annotations

from _shared import build_respan, example_scope
from agentops import task, trace


def main() -> None:
    respan = build_respan(
        example_name="expected-failure",
        workflow_name="agentops_expected_failure",
    )

    @task(name="deterministic_failure")
    def deterministic_failure() -> None:
        raise RuntimeError("deterministic AgentOps task failure")

    @trace(name="agentops_expected_failure")
    def workflow() -> dict[str, str]:
        try:
            deterministic_failure()
        except RuntimeError as exc:
            return {"caught": str(exc)}
        raise AssertionError("the deterministic task should fail")

    with example_scope("expected-failure"):
        try:
            print(workflow())
        finally:
            respan.shutdown()


if __name__ == "__main__":
    main()
