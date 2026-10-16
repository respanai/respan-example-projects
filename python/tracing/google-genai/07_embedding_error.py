"""Controlled error scenario; no Google provider request is sent."""

from __future__ import annotations

from _fixtures import make_fixture_client
from _shared import example_attributes, make_respan, print_result, workflow_name
from google.genai import errors
from respan import workflow

EXAMPLE_NAME = "embedding-error"


@workflow(name=workflow_name(EXAMPLE_NAME))
def embedding_error() -> str:
    client = make_fixture_client()
    try:
        try:
            client.models.embed_content(
                model="invalid-fixture-model", contents="controlled error"
            )
        except errors.ClientError:
            return "Expected SDK error preserved and traced."
        raise AssertionError("The controlled SDK error did not occur")
    finally:
        client.close()


def main() -> None:
    respan = make_respan(EXAMPLE_NAME)
    try:
        with example_attributes(EXAMPLE_NAME) as identifier:
            print_result(EXAMPLE_NAME, identifier, embedding_error())
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
