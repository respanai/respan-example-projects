"""Latest native customizers remain in the export path and run once per record."""

import braintrust
from _shared import (
    create_braintrust_logger,
    create_respan,
    new_run_id,
    workflow_context,
)

NAME = "08_customizers"
WORKFLOW = "Braintrust Customizers"


def main():
    if not hasattr(braintrust, "set_span_customizers"):
        print("SKIP: native export customizers require a newer Braintrust SDK")
        return
    marker = new_run_id(NAME)
    respan = create_respan(workflow_name=WORKFLOW, run_id=marker, example_name=NAME)
    logger = create_braintrust_logger(workflow_name=WORKFLOW)

    class Customizer(braintrust.SpanCustomizer):
        def on_span_export(self, record):
            if "output" in record:
                record["output"] = {"customized": "native SDK output"}
            return record

    braintrust.set_span_customizers([Customizer()])
    try:
        with (
            workflow_context(
                respan, workflow_name=WORKFLOW, run_id=marker, example_name=NAME
            ),
            logger.start_span(name=WORKFLOW, type="tool") as span,
        ):
            span.log(input={"value": 1}, output={"original": "value"})
        print("Actual native customized record retained")
    finally:
        logger.flush()
        braintrust.set_span_customizers(None)
        respan.shutdown()


if __name__ == "__main__":
    main()
