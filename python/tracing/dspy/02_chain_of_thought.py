"""Trace DSPy's ChainOfThought module with a typed Signature."""

from __future__ import annotations

import dspy
from _shared import managed_example, print_result, traced_example


class IncidentSummary(dspy.Signature):
    """Summarize an incident and include the most likely next action."""

    incident: str = dspy.InputField()
    summary: str = dspy.OutputField()


def run_chain_of_thought_example() -> None:
    with managed_example(
        app_name="dspy-02-chain-of-thought",
        example_name="02_chain_of_thought",
        temperature=0.1,
    ) as context:
        summarize = dspy.ChainOfThought(IncidentSummary)
        incident = (
            "A support bot produced slow responses after a prompt update. "
            "The trace shows longer retrieval time and two extra LLM calls."
        )

        with traced_example(context, input_data={"incident": incident}) as span:
            prediction = summarize(incident=incident)
            span.set_output(
                {
                    "reasoning": prediction.reasoning,
                    "summary": prediction.summary,
                }
            )

        print_result("Summary", prediction.summary)


if __name__ == "__main__":
    run_chain_of_thought_example()
