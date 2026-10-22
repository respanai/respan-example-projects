"""Exercise newer public resource clients when the installed SDK exposes them."""

import base64

from _fixture import PROJECT_ID
from _shared import example, print_result


def main():
    with example("05_new_rest_resources") as client:
        for resource in ("traces", "audit_logs", "integrations", "webhooks"):
            if resource not in client._SUBCLIENTS:
                print("Skipped absent SDK resource: " + resource)
                continue
            if resource == "traces":
                result = client.traces.list(project=PROJECT_ID)
            elif resource == "webhooks":
                result = client.webhooks.list(
                    organization=base64.b64encode(b"Organization:fixture").decode()
                )
            else:
                result = getattr(client, resource).list()
            print_result(resource, result)


if __name__ == "__main__":
    main()
