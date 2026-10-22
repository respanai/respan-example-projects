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

EXAMPLE = "embedding"
RUN_MARKER = marker()
respan = make_respan(EXAMPLE, RUN_MARKER)
logger = make_logger()


@workflow(name="helicone_embedding")
def run(text: str) -> int:
    vector = [round((index - 128) / 128, 8) for index in range(256)]

    def operation(recorder):
        response = {
            "model": "local-helicone-embedding",
            "data": [{"index": 0, "embedding": vector}],
            "usage": {"prompt_tokens": 3, "total_tokens": 3},
        }
        recorder.append_results(response)
        return len(vector)

    return logger.log_request(
        request={
            "_type": "embedding",
            "model": "local-helicone-embedding",
            "input": [text],
        },
        operation=operation,
        provider="custom-embedding-provider",
    )


try:
    with example_attributes(EXAMPLE, RUN_MARKER, execution_id(), mode="local"):
        dimensions = run("Embed this exact deterministic value.")
    assert dimensions == 256
    assert_local_logs(1)
    print_result(
        EXAMPLE,
        RUN_MARKER,
        {"dimensions": dimensions, "full_vector_logged": True, "local_logs": 1},
    )
finally:
    finish_respan(respan)
