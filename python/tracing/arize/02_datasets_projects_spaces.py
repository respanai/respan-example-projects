"""Exercise native REST dataset creation with a full vector dataframe."""

import pandas as pd
from _fixture import SPACE_ID
from _shared import example, print_result


def main():
    with example("02_datasets_projects_spaces") as client:
        print_result("Dataset page", client.datasets.list(space=SPACE_ID))
        frame = pd.DataFrame(
            [
                {
                    "input": {"embedding": [float(i) for i in range(3072)]},
                    "output": "controlled expected",
                }
            ]
        )
        print_result(
            "Created fixture dataset",
            client.datasets.create(
                name="fixture-dataset", space=SPACE_ID, examples=frame, force_http=True
            ),
        )
        print_result("Project page", client.projects.list(space=SPACE_ID))


if __name__ == "__main__":
    main()
