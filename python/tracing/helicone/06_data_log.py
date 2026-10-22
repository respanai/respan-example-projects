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

EXAMPLE = "data-log"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_data_log")
def run(query_name: str) -> dict:
    def operation(recorder):
        result = {
            "_type": "data",
            "name": query_name,
            "status": "success",
            "rows": [{"active_users": 3}],
        }
        recorder.append_results(result)
        return result

    return logger.log_request(
        request={
            "_type": "data",
            "name": query_name,
            "query": "SELECT count(*) AS active_users FROM users",
            "database": "local-fixture",
        },
        operation=operation,
        additional_headers={"Helicone-Property-Component": "database"},
    )


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        result = run("active_user_query")
    assert_local_logs(1)
    print_result(EXAMPLE, RUN_MARKER, {"result": result, "local_logs": 1})
finally:
    finish_respan(respan)
