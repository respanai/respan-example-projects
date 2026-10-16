"""Native SDK generator protocol; upstream context/return quirks remain."""

from _shared import build_respan
from agentops import task


def main():
    telemetry = build_respan(
        example_name="generator", workflow_name="agentops_generator"
    )

    @task(name="native_generator")
    def generate():
        value = yield "first"
        yield value
        return "upstream SDK consumes this return"

    try:
        iterator = generate()
        assert next(iterator) == "first"
        assert iterator.send("second") == "second"
        try:
            next(iterator)
        except StopIteration as end:
            assert end.value is None
        else:
            raise AssertionError("Native generator must finish")
    finally:
        telemetry.shutdown()


if __name__ == "__main__":
    main()
