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
from pydantic import BaseModel
from respan import workflow

EXAMPLE_NAME = "structured-chat"


class Weather(BaseModel):
    city: str


@workflow(name=workflow_name(EXAMPLE_NAME))
def trace_structured(prompt: str):
    client = make_client()
    try:
        result = client.chat.completions.parse(
            model="fixture-model",
            messages=[{"role": "user", "content": prompt}],
            response_format=Weather,
        )
        with client.chat.completions.stream(
            model="fixture-model", messages=[{"role": "user", "content": prompt}]
        ) as stream:
            final = stream.get_final_completion()
        return {
            "parsed_city": result.choices[0].message.parsed.city,
            "manager_content": final.choices[0].message.content,
        }
    finally:
        client.close()


def main():
    run = marker()
    respan = make_respan(EXAMPLE_NAME, run)
    try:
        with example_attributes(EXAMPLE_NAME, run, execution_id(), mode="fixture"):
            print_result(EXAMPLE_NAME, run, trace_structured("Return the city."))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
