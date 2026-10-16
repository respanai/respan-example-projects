from _shared import make_custom_identifier, make_event, tracing


def main():
    marker = make_custom_identifier("current-hooks")
    with tracing("current-hooks", run_id=marker) as (inst, memory):
        rows = [
            ("beforeSubmitPrompt", {"prompt": "Controlled current hook transcript"}),
            (
                "preToolUse",
                {
                    "tool_name": "Read",
                    "tool_input": {"path": "/synthetic.py"},
                    "tool_use_id": "current-read",
                },
            ),
            (
                "postToolUse",
                {
                    "tool_name": "Read",
                    "tool_input": {"path": "/synthetic.py"},
                    "tool_output": '{"content":"fixture"}',
                    "tool_use_id": "current-read",
                },
            ),
            (
                "postToolUseFailure",
                {
                    "tool_name": "Shell",
                    "tool_input": {"command": "fixture"},
                    "tool_use_id": "current-failure",
                    "failure_type": "timeout",
                    "error_message": "Controlled timeout",
                },
            ),
            (
                "subagentStart",
                {
                    "subagent_id": "sub-fixture",
                    "subagent_type": "explore",
                    "task": "Controlled exploration",
                    "tool_call_id": "current-subagent",
                },
            ),
            (
                "subagentStop",
                {
                    "subagent_id": "sub-fixture",
                    "subagent_type": "explore",
                    "summary": "Fixture findings",
                    "status": "completed",
                },
            ),
            (
                "preCompact",
                {
                    "trigger": "manual",
                    "context_tokens": 120000,
                    "context_window_size": 128000,
                },
            ),
            ("afterAgentResponse", {"text": "First fixture message"}),
            ("afterAgentResponse", {"text": "Second fixture message"}),
            ("stop", {"status": "completed", "loop_count": 0}),
        ]
        for name, fields in rows:
            inst.process_event(make_event("current-hooks", marker, name, **fields))
        assert len(memory.get_finished_spans()) == 8


if __name__ == "__main__":
    main()
