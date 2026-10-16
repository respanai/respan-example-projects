from __future__ import annotations

from _shared import (
    example_attributes,
    finish_respan,
    image_model_name,
    make_client,
    make_custom_identifier,
    make_respan,
    print_result,
    print_start,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "image-generation"


@workflow(name=workflow_name(EXAMPLE_NAME))
def _image_generation_workflow(prompt: str) -> str:
    with make_client() as client:
        response = client.images.generate(
            model=image_model_name(),
            prompt=prompt,
            n=1,
            width=256,
            height=256,
            steps=4,
            response_format="b64_json",
        )
        data = getattr(response, "data", None) or []
        if not data:
            return "no image results"
        first = data[0]
        image_type = getattr(first, "type", "unknown")
        return f"image_count={len(data)} first_type={image_type}"


def run_image_generation() -> None:
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    respan = make_respan(EXAMPLE_NAME, custom_identifier)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print_start(EXAMPLE_NAME, custom_identifier)
            text = _image_generation_workflow(
                "A small line-art observability dashboard icon"
            )
    finally:
        finish_respan(respan)

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    run_image_generation()
