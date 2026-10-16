"""Trace DSPy's Evaluate API on a small program/devset."""

from __future__ import annotations

import dspy
from _shared import managed_example, print_result, traced_example


class CapitalQuestion(dspy.Signature):
    """Answer the capital-city question."""

    question: str = dspy.InputField()
    answer: str = dspy.OutputField()


class CapitalAnswerer(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.answer = dspy.Predict(CapitalQuestion)

    def forward(self, question: str) -> dspy.Prediction:
        prediction = self.answer(question=question)
        return dspy.Prediction(answer=prediction.answer)


def contains_expected_answer(example: dspy.Example, prediction: dspy.Prediction) -> int:
    return int(example.answer.lower() in prediction.answer.lower())


def run_evaluate_program_example() -> None:
    with managed_example(
        app_name="dspy-06-evaluate-program",
        example_name="06_evaluate_program",
        temperature=0.0,
    ) as context:
        program = CapitalAnswerer()
        devset = [
            dspy.Example(
                question="What is the capital of France?",
                answer="Paris",
            ).with_inputs("question")
        ]
        evaluator = dspy.Evaluate(
            devset=devset,
            metric=contains_expected_answer,
            num_threads=1,
            display_progress=False,
            display_table=False,
        )

        with traced_example(
            context,
            input_data={
                "devset_size": len(devset),
                "questions": [example.question for example in devset],
            },
        ) as span:
            result = evaluator(program)
            span.set_output({"score": result.score})

        print_result("Score", result.score)


if __name__ == "__main__":
    run_evaluate_program_example()
