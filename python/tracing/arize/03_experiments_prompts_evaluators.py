"""Run the SDK's own dry-run helper and retain its native tracing/result."""

from _fixture import DATASET_ID, SPACE_ID
from _shared import example, print_result


def task(input):
    return "controlled experiment task result"


def main():
    with example("03_experiments_prompts_evaluators") as client:
        result = client.experiments.run(
            name="controlled-dry-run",
            dataset=DATASET_ID,
            task=task,
            dry_run=True,
            force_http=True,
            concurrency=1,
        )
        assert result[0] is None
        print_result("Native result frame", result[1])
        print_result("Prompt page", client.prompts.list(space=SPACE_ID))
        print_result("Evaluator page", client.evaluators.list(space=SPACE_ID))


if __name__ == "__main__":
    main()
