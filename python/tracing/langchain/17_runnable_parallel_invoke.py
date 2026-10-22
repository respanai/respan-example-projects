"""RunnableParallel invoke."""

from _shared import init_telemetry, tracing_config
from langchain_core.runnables import RunnableLambda, RunnableParallel


def runnable_parallel_invoke() -> None:
    init_telemetry("langchain-runnable-parallel-invoke")
    runnable = RunnableParallel(
        uppercase=RunnableLambda(lambda text: text.upper()),
        length=RunnableLambda(lambda text: len(text)),
    )
    response = runnable.invoke(
        "respan",
        config=tracing_config("runnable_parallel_invoke"),
    )
    print(response)


if __name__ == "__main__":
    runnable_parallel_invoke()
