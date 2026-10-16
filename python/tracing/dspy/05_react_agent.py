"""Trace a DSPy ReAct program that can call a Python tool."""

from __future__ import annotations

import dspy
from _shared import managed_example, print_result, traced_example


class CityQuestion(dspy.Signature):
    """Answer the user's city question with one sentence."""

    question: str = dspy.InputField()
    answer: str = dspy.OutputField()


def lookup_city_fact(city: str) -> str:
    facts = {
        "tokyo": "Tokyo has one of the world's busiest rail networks.",
        "paris": "Paris is known for the Louvre and the Eiffel Tower.",
        "seattle": "Seattle is known for coffee culture and cloud computing.",
    }
    return facts.get(city.lower(), f"No stored fact for {city}.")


def run_react_agent_example() -> None:
    with managed_example(
        app_name="dspy-05-react-agent",
        example_name="05_react_agent",
        temperature=0.0,
    ) as context:
        agent = dspy.ReAct(CityQuestion, tools=[lookup_city_fact], max_iters=3)
        question = (
            "Use lookup_city_fact for Tokyo, then answer with the fact in one sentence."
        )

        with traced_example(context, input_data={"question": question}) as span:
            prediction = agent(question=question)
            span.set_output({"answer": prediction.answer})

        print_result("Answer", prediction.answer)


if __name__ == "__main__":
    run_react_agent_example()
