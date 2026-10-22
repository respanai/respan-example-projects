"""Native input/output guardrail decorators preserve actual results."""

from _shared import build_respan
from agentops import guardrail, trace


def main():
    telemetry = build_respan(
        example_name="guardrail", workflow_name="agentops_guardrail"
    )

    @guardrail(name="input_check", spec="input")
    def input_check(value):
        return {"allowed": bool(value)}

    @guardrail(name="output_check", spec="output")
    def output_check(value):
        return value

    @trace(name="guardrail_workflow")
    def run():
        return output_check(input_check("controlled"))

    try:
        assert run() == {"allowed": True}
    finally:
        telemetry.shutdown()


if __name__ == "__main__":
    main()
