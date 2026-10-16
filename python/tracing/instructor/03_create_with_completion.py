"""Return the parsed model and a bounded provider completion summary."""

from __future__ import annotations

from typing import Literal

from _respan_instructor import create_respan_instructor_client, workflow
from pydantic import BaseModel
from respan_tracing.exporters import propagate_attributes


class ReleaseNote(BaseModel):
    title: str
    category: Literal["feature", "fix", "docs"]
    user_visible: bool
    bullets: list[str]


@workflow(name="instructor_example_03_create_with_completion")
def draft_release_note(client, scenario: str) -> tuple[ReleaseNote, dict[str, object]]:
    release_note, completion = client.create_with_completion(
        response_model=ReleaseNote,
        messages=[
            {
                "role": "user",
                "content": (
                    "Create a concise release note for a fix that preserves full "
                    "Instructor tool schemas in traced Respan spans. Include two "
                    "or three user-visible bullets."
                ),
            }
        ],
    )
    return release_note, {
        "completion_type": type(completion).__name__,
        "completion_id": getattr(completion, "id", None),
        "completion_model": getattr(completion, "model", None),
    }


def run_create_with_completion_example() -> None:
    respan, client = create_respan_instructor_client(
        app_name="instructor-create-with-completion",
        payload={
            "title": "Canonical tracing",
            "category": "fix",
            "user_visible": True,
            "bullets": ["Complete schemas", "Actual tool IDs"],
        },
    )

    try:
        with propagate_attributes(
            thread_identifier="instructor_example_03_create_with_completion",
            metadata={
                "example_script": "03_create_with_completion.py",
                "instructor_api": "create_with_completion",
            },
        ):
            release_note, completion_summary = draft_release_note(
                client,
                "draft a deterministic release note",
            )

        print(dict(release_note))
        print(completion_summary)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    run_create_with_completion_example()
