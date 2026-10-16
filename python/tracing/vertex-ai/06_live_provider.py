import os

import vertexai
from _shared import REPO_ROOT, create_respan, example_context, finish_respan
from dotenv import load_dotenv
from respan import workflow
from vertexai.generative_models import GenerativeModel


@workflow(name="vertexai_live")
def generate(prompt):
    return (
        GenerativeModel(os.getenv("VERTEXAI_MODEL", "gemini-2.5-flash"))
        .generate_content(prompt)
        .text
    )


def main():
    if os.getenv("VERTEXAI_EXAMPLE_LIVE") != "1":
        print("live-provider: skipped (set VERTEXAI_EXAMPLE_LIVE=1 to opt in)")
        return
    load_dotenv(REPO_ROOT / ".env", override=False)
    vertexai.init(
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.environ["GOOGLE_CLOUD_LOCATION"],
    )
    respan = create_respan()
    try:
        with example_context("live"):
            print(generate("Reply with one short sentence about tracing."))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
