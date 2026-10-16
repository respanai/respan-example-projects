"""Extract a typed response with Instructor.create."""

from __future__ import annotations

from _respan_instructor import create_respan_instructor_client, workflow
from pydantic import BaseModel
from respan_tracing.exporters import propagate_attributes


class InvoiceSummary(BaseModel):
    vendor: str
    invoice_id: str
    currency: str
    item_count: int
    total_usd: float


@workflow(name="instructor_example_01_create")
def extract_invoice(client, scenario: str) -> InvoiceSummary:
    return client.create(
        response_model=InvoiceSummary,
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract this invoice: Northwind Cloud invoice NW-1042 in USD. "
                    "Line one is SKU LOG-001, log retention, 2 units at 49.50. "
                    "Line two is SKU SEC-010, security review, 1 unit at 199.00. "
                    "The invoice total is 298.00 USD."
                ),
            }
        ],
    )


def run_create_example() -> None:
    respan, client = create_respan_instructor_client(
        app_name="instructor-create",
        payload={
            "vendor": "Northwind Cloud",
            "invoice_id": "NW-1042",
            "currency": "USD",
            "item_count": 3,
            "total_usd": 298.0,
        },
    )
    try:
        with propagate_attributes(
            thread_identifier="instructor_example_01_create",
            metadata={"example_script": "01_create.py", "instructor_api": "create"},
        ):
            invoice = extract_invoice(client, "extract a deterministic invoice")

        print(dict(invoice))
    finally:
        respan.shutdown()


if __name__ == "__main__":
    run_create_example()
