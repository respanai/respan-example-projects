from __future__ import annotations

from _shared import make_custom_identifier, make_event, replay_events

EXAMPLE_NAME = "full-transcript"


def main() -> None:
    run_id = make_custom_identifier(EXAMPLE_NAME)
    events = [
        make_event(
            EXAMPLE_NAME,
            run_id,
            "beforeSubmitPrompt",
            prompt="Add a command line flag, update docs, run the focused test.",
            attachments=[{"path": "README.md"}, {"path": "cli.py"}],
        ),
        make_event(
            EXAMPLE_NAME,
            run_id,
            "afterAgentThought",
            text="I need to inspect the parser setup before editing the docs.",
            duration_ms=260,
        ),
        make_event(
            EXAMPLE_NAME,
            run_id,
            "afterShellExecution",
            command='rg -n "ArgumentParser|--verbose" .',
            output="cli.py:10:parser = argparse.ArgumentParser()",
            duration=150,
        ),
        make_event(
            EXAMPLE_NAME,
            run_id,
            "afterFileEdit",
            file_path="/workspace/cli.py",
            edits=[
                {
                    "oldText": "parser = argparse.ArgumentParser()",
                    "newText": "parser = argparse.ArgumentParser()\nparser.add_argument('--verbose', action='store_true')",
                    "startLine": 10,
                    "endLine": 10,
                }
            ],
        ),
        make_event(
            EXAMPLE_NAME,
            run_id,
            "afterMCPExecution",
            tool_name="read_documentation",
            tool_input={"topic": "argparse boolean flags"},
            result_json={"summary": "Use store_true for boolean flags."},
            duration_ms=190,
        ),
        make_event(
            EXAMPLE_NAME,
            run_id,
            "afterAgentResponse",
            text="Added the verbose flag, updated usage docs, and ran the focused parser test.",
        ),
        make_event(EXAMPLE_NAME, run_id, "stop", status="completed", loop_count=1),
    ]
    replay_events(EXAMPLE_NAME, events, run_id=run_id)


if __name__ == "__main__":
    main()
