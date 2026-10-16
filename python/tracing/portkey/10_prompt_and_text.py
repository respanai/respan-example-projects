from _shared import (
    example_attributes,
    execution_id,
    finish_respan,
    make_client,
    make_respan,
    marker,
    print_result,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "prompt-and-text"


@workflow(name=workflow_name(EXAMPLE_NAME))
def trace_prompt(prompt: str):
    client = make_client()
    try:
        saved = client.prompts.completions.create(
            prompt_id="fixture-prompt", variables={"request": prompt}
        )
        text = client.completions.create(model="fixture-text", prompt=prompt)
        return {
            "prompt_result": saved.choices[0].message.content,
            "text_result": text.choices[0].text,
        }
    finally:
        client.close()


def main():
    run = marker()
    respan = make_respan(EXAMPLE_NAME, run)
    try:
        with example_attributes(EXAMPLE_NAME, run, execution_id(), mode="fixture"):
            print_result(EXAMPLE_NAME, run, trace_prompt("Say hello."))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
