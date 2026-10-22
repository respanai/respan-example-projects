from __future__ import annotations

from _shared import (
    assert_local_logs,
    example_attributes,
    execution_id,
    finish_respan,
    make_logger,
    make_respan,
    marker,
    print_result,
)
from respan import workflow

EXAMPLE = "vector-db-log"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_vector_db_log")
def run(query: str) -> list[dict]:
    def operation(recorder):
        results = [
            {"id": "doc-1", "score": 0.98, "text": "Manual logger documentation"},
            {"id": "doc-2", "score": 0.91, "text": "Tracing contract"},
        ]
        recorder.append_results({"matches": results})
        return results

    return logger.log_request(
        request={
            "_type": "vector_db",
            "operation": "search",
            "databaseName": "local-docs",
            "text": query,
            "vector": [0.1, 0.2, 0.3, 0.4],
            "topK": 2,
        },
        operation=operation,
    )


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        matches = run("How is Helicone traced?")
    assert_local_logs(1)
    print_result(EXAMPLE, RUN_MARKER, {"matches": matches, "local_logs": 1})
finally:
    finish_respan(respan)
