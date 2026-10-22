"""Run released example mutation validation and REST request construction."""

from _fixture import DATASET_ID
from _shared import example, print_result


def main():
    with example("06_dataset_mutations") as client:
        if not hasattr(client.datasets, "update_examples"):
            print("Skipped absent dataset example mutation APIs")
            return
        updated = client.datasets.update_examples(
            dataset=DATASET_ID,
            examples=[
                {
                    "id": "example-fixture",
                    "input": {"sparse": {i: float(i) for i in range(256)}},
                }
            ],
        )
        print_result("Native update", updated)
        deleted = client.datasets.delete_examples(
            dataset=DATASET_ID,
            dataset_version_id="version-fixture",
            examples=["example-fixture"],
        )
        assert deleted.completed
        print_result("Native delete", deleted)


if __name__ == "__main__":
    main()
