from __future__ import annotations

from _shared import make_custom_identifier, make_event, replay_events

EXAMPLE_NAME = "agent-turn"


def main() -> None:
    run_id = make_custom_identifier(EXAMPLE_NAME)
    events = [
        make_event(
            EXAMPLE_NAME,
            run_id,
            "beforeSubmitPrompt",
            prompt="Create a small Python function that validates an email address.",
            attachments=[],
        ),
        make_event(
            EXAMPLE_NAME,
            run_id,
            "afterAgentThought",
            text="I should implement a simple regex helper and keep it easy to test.",
            duration_ms=420,
        ),
        make_event(
            EXAMPLE_NAME,
            run_id,
            "afterFileEdit",
            file_path="/workspace/email_utils.py",
            edits=[
                {
                    "oldText": "",
                    "newText": "def is_email(value: str) -> bool:\n    return '@' in value",
                    "startLine": 1,
                    "endLine": 2,
                }
            ],
        ),
        make_event(
            EXAMPLE_NAME,
            run_id,
            "afterAgentResponse",
            text="Implemented the email helper and kept the validation logic compact.",
        ),
    ]
    events.append(make_event(EXAMPLE_NAME, run_id, "stop", status="completed"))
    replay_events(EXAMPLE_NAME, events, run_id=run_id)


if __name__ == "__main__":
    main()
