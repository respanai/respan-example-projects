"""Exercise native memory telemetry without a storage service."""

from _shared import create_respan, finish_respan, new_run_id
from respan import propagate_attributes, workflow
from strands.telemetry import get_tracer

WORKFLOW_NAME = "Strands Memory Telemetry Example"


def main() -> None:
    native = get_tracer()
    if not hasattr(native, "start_memory_search_span"):
        print({"skipped": "native memory telemetry unavailable in installed Strands"})
        return
    from strands.memory.types import MemoryEntry

    run_id = new_run_id("memory")
    respan = create_respan("memory_telemetry", run_id)
    try:

        @workflow(name=WORKFLOW_NAME)
        def run_workflow(query: str) -> dict[str, int]:
            span = native.start_memory_search_span(query, ["fixture-memory-store"])
            entries = [
                MemoryEntry(
                    content="controlled memory result",
                    store_name="fixture-memory-store",
                    metadata={"source": "fixture"},
                )
            ]
            native.end_memory_search_span(span, entries)
            return {"results": len(entries)}

        with propagate_attributes(
            metadata={"run_id": run_id, "script": "10_memory_telemetry.py"}
        ):
            print(run_workflow("controlled memory query"))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
