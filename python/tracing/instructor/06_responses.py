"""Current provider factory and OpenAI Responses structured output."""

import instructor
from _respan_instructor import (
    User,
    attributes,
    create_respan_instructor_client,
    workflow,
)


@workflow(name="instructor_example_06_responses")
def extract(client):
    parsed, completion = client.responses.create_with_completion(
        response_model=User, messages="Extract Ada, age36."
    )
    assert parsed.age == 36
    return {"parsed": parsed.model_dump(), "response_id": completion.id}


def main():
    if not hasattr(instructor.Mode, "RESPONSES_TOOLS") or not hasattr(
        instructor, "from_provider"
    ):
        print("SKIP: minimum native SDK predates Responses/provider factory")
        return
    tracing, client = create_respan_instructor_client(
        app_name="instructor-responses", responses=True, from_provider=True
    )
    try:
        with attributes("06_responses.py"):
            print(extract(client))
    finally:
        tracing.shutdown()


if __name__ == "__main__":
    main()
