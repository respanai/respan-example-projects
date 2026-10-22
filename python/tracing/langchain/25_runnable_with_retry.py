"""Runnable with_retry."""

from _shared import init_telemetry, tracing_config
from langchain_core.runnables import RunnableLambda


def runnable_with_retry() -> None:
    init_telemetry("langchain-runnable-with-retry")
    attempts = {"count": 0}

    def flaky(text: str) -> str:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("transient failure")
        return f"recovered: {text}"

    runnable = RunnableLambda(flaky).with_retry(stop_after_attempt=2)
    response = runnable.invoke(
        "respan",
        config=tracing_config("runnable_with_retry"),
    )
    print(response)


if __name__ == "__main__":
    runnable_with_retry()
