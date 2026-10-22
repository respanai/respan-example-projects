from _shared import make_custom_identifier, make_event, tracing


def main():
    marker = make_custom_identifier("stop-cleanup")
    with tracing("stop-cleanup", run_id=marker) as (inst, memory):
        inst.process_event(
            make_event(
                "stop-cleanup",
                marker,
                "beforeSubmitPrompt",
                prompt="Start a controlled turn",
            )
        )
        inst.process_event(
            make_event(
                "stop-cleanup", marker, "afterAgentThought", text="Fixture reasoning"
            )
        )
        result = inst.process_event(
            make_event("stop-cleanup", marker, "stop", status="aborted", loop_count=0)
        )
        assert result.emitted
        assert not inst.process_event(
            make_event("stop-cleanup", marker, "stop", status="aborted")
        ).emitted
        assert memory.get_finished_spans()[-1].status.status_code.name == "ERROR"


if __name__ == "__main__":
    main()
