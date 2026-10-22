from __future__ import annotations

from _shared import (
    example_attributes,
    execution_id,
    finish_respan,
    live_configured,
    make_logger,
    make_respan,
    marker,
    print_result,
)
from respan import workflow

EXAMPLE = "live-helicone"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)


@workflow(name="helicone_live_manual_log")
def run(message: str) -> str:
    logger = make_logger(live=True)

    def operation(recorder):
        response = {
            "_type": "data",
            "name": "respan_live_validation",
            "status": "success",
            "message": message,
        }
        recorder.append_results(response)
        return "live-log-attempted"

    return logger.log_request(
        request={
            "_type": "data",
            "name": "respan_live_validation",
            "message": message,
        },
        operation=operation,
        additional_headers={"Helicone-Property-Source": "respan-example"},
    )


try:
    if not live_configured():
        print_result(EXAMPLE, RUN_MARKER, {"skipped": "HELICONE_API_KEY is not set"})
    else:
        with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="live"):
            outcome = run("Validate the Respan Helicone instrumentation.")
        print_result(
            EXAMPLE,
            RUN_MARKER,
            {
                "outcome": outcome,
                "live": True,
                "verified": False,
                "note": "Verify acceptance in Helicone; the SDK swallows transport failures.",
            },
        )
finally:
    finish_respan(respan)
