import os

from _shared import (
    example_attributes,
    finish_respan,
    make_client,
    make_custom_identifier,
    make_respan,
    model_name,
)
from respan import workflow


@workflow(name="together_live")
def invoke(prompt):
    with make_client() as client:
        return (
            client.chat.completions.create(
                model=model_name(), messages=[{"role": "user", "content": prompt}]
            )
            .choices[0]
            .message.content
        )


def main():
    if os.getenv("RESPAN_TOGETHER_LIVE") != "1":
        print("live-provider: skipped (set RESPAN_TOGETHER_LIVE=1)")
        return
    marker = make_custom_identifier("live")
    respan = make_respan("live", marker)
    try:
        with example_attributes("live", marker):
            print(invoke("Reply with one short sentence about tracing."))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
