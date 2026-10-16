"""Public native trace lifecycle and dynamic metadata updates."""

import agentops
from _shared import build_respan


def main():
    telemetry = build_respan(
        example_name="manual-metadata", workflow_name="agentops_manual_metadata"
    )
    try:
        native = agentops.start_trace("manual_metadata", tags=["controlled", "manual"])
        assert native is not None
        assert agentops.update_trace_metadata(
            {"stage": "controlled", "labels": ["alpha", "beta"]}
        )
        agentops.end_trace(native, "Success")
        failed = agentops.start_trace("manual_failure")
        agentops.end_trace(failed, "Error")
    finally:
        telemetry.shutdown()


if __name__ == "__main__":
    main()
