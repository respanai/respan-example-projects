from __future__ import annotations

from _shared import make_custom_identifier, make_event, replay_events

EXAMPLE_NAME = "terminal-and-mcp-tools"


def main() -> None:
    run_id = make_custom_identifier(EXAMPLE_NAME)
    events = [
        make_event(
            EXAMPLE_NAME,
            run_id,
            "beforeSubmitPrompt",
            prompt="Find the FastAPI routes and summarize the health endpoint.",
            attachments=[{"path": "app/main.py"}],
        ),
        make_event(
            EXAMPLE_NAME,
            run_id,
            "afterShellExecution",
            command='rg -n "health|FastAPI" app',
            output="app/main.py:8:app = FastAPI()\napp/main.py:19:@app.get('/health')",
            duration=160,
        ),
        make_event(
            EXAMPLE_NAME,
            run_id,
            "afterMCPExecution",
            tool_name="search_codebase",
            tool_input={"query": "health endpoint", "path": "app"},
            result_json={"matches": [{"path": "app/main.py", "line": 19}]},
            duration_ms=210,
        ),
        make_event(
            EXAMPLE_NAME,
            run_id,
            "afterAgentResponse",
            text="The health endpoint is defined in app/main.py and returns service status.",
        ),
    ]
    events.append(make_event(EXAMPLE_NAME, run_id, "stop", status="completed"))
    replay_events(EXAMPLE_NAME, events, run_id=run_id)


if __name__ == "__main__":
    main()
