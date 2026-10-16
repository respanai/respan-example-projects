"""Chain error."""

from _shared import init_telemetry, tracing_config
from langchain_core.runnables import RunnableLambda


def chain_error() -> None:
    init_telemetry("langchain-chain-error")

    def fail(_: str) -> str:
        raise RuntimeError("chain failed")

    runnable = RunnableLambda(fail)
    try:
        runnable.invoke("trigger", config=tracing_config("chain_error"))
    except RuntimeError as exc:
        print(f"caught: {exc}")


if __name__ == "__main__":
    chain_error()
