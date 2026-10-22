"""Read native admin pages through generated REST parsing."""

from _fixture import SPACE_ID
from _shared import example, print_result


def main():
    with example("04_admin_operations") as client:
        print_result("Role page", client.roles.list())
        print_result(
            "Annotation config page", client.annotation_configs.list(space=SPACE_ID)
        )


if __name__ == "__main__":
    main()
