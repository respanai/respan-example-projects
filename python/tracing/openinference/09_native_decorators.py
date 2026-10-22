from __future__ import annotations

from _shared import (
    example_attributes,
    example_run_id,
    finish_respan,
    make_respan,
    print_result,
    tracer,
    workflow,
    workflow_name,
)
from openinference.instrumentation import OITracer, TraceConfig

EXAMPLE_NAME = "native-decorators"


@workflow(name=workflow_name(EXAMPLE_NAME))
def work():
    native = OITracer(tracer(), config=TraceConfig())
    kinds = ("retriever", "reranker", "guardrail", "evaluator")
    if any(not hasattr(native, kind) for kind in kinds):
        print("SKIP: new native decorators absent in OpenInference0.1.32")
        return "explicit version skip"
    for kind in kinds:
        value = {"kind": kind, "fixture": "controlled-result"}

        def operation(value=value):
            return value

        wrapped = getattr(native, kind)(operation, name=kind)
        assert wrapped() is value
    return "retriever, reranker, guardrail and evaluator native decorators"


def run():
    marker = example_run_id()
    telemetry = make_respan(EXAMPLE_NAME, marker)
    try:
        with example_attributes(EXAMPLE_NAME, marker):
            result = work()
    finally:
        finish_respan(telemetry)
    print_result(EXAMPLE_NAME, marker, result)


if __name__ == "__main__":
    run()
