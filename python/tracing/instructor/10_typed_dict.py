"""Current native TypedDict response, preserving its dictionary return type."""

from typing import TypedDict

import instructor
from _respan_instructor import attributes, create_respan_instructor_client, workflow


class Invoice(TypedDict):
    vendor: str
    amount: float


@workflow(name="instructor_example_10_typed_dict")
def extract(client):
    result = client.create(
        response_model=Invoice,
        messages=[{"role": "user", "content": "Northwind invoice, amount298."}],
    )
    value = result if isinstance(result, dict) else result.model_dump()
    assert value["vendor"] == "Northwind"
    return {"native_return_type": type(result).__name__, "value": value}


def main():
    if not hasattr(instructor, "from_provider"):
        print("SKIP: minimum native SDK predates maintained TypedDict support")
        return
    tracing, client = create_respan_instructor_client(
        app_name="instructor-typed-dict",
        payload={"vendor": "Northwind", "amount": 298.0},
    )
    try:
        with attributes("10_typed_dict.py"):
            print(extract(client))
    finally:
        tracing.shutdown()


if __name__ == "__main__":
    main()
