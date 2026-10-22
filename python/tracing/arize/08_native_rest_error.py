"""Preserve the generated native404 exception without an invented error output."""

from _shared import example
from arize._generated.api_client.exceptions import NotFoundException


def main():
    try:
        with example("08_native_rest_error", failure=True) as client:
            client.datasets.list()
    except NotFoundException as error:
        assert error.status == 404
        print("Expected native error: " + type(error).__name__)
    else:
        raise AssertionError("Controlled native error was not raised")


if __name__ == "__main__":
    main()
