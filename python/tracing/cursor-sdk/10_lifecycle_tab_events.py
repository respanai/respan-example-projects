from _shared import tracing


def main():
    with tracing("lifecycle-tab-events") as (inst, memory):
        for event in [
            {
                "hook_event_name": "sessionStart",
                "session_id": "session-fixture",
                "composer_mode": "agent",
                "is_background_agent": False,
            },
            {
                "hook_event_name": "beforeTabFileRead",
                "file_path": "/synthetic.py",
                "content": "fixture = 1",
            },
            {
                "hook_event_name": "afterTabFileEdit",
                "file_path": "/synthetic.py",
                "edits": [
                    {
                        "old_string": "fixture = 1",
                        "new_string": "fixture = 2",
                        "range": {"start_line_number": 1, "end_line_number": 1},
                    }
                ],
            },
            {
                "hook_event_name": "sessionEnd",
                "session_id": "session-fixture",
                "reason": "completed",
                "duration_ms": 1000,
                "final_status": "completed",
            },
            {"hook_event_name": "workspaceOpen", "workspace_roots": ["/synthetic"]},
        ]:
            assert inst.process_event(event).emitted
        assert len(memory.get_finished_spans()) == 5


if __name__ == "__main__":
    main()
