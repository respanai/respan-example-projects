"""Private native model content and instrumentation suppression."""

from _respan_instructor import (
    User,
    attributes,
    create_respan_instructor_client,
    workflow,
)
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


@workflow(name="instructor_example_09_privacy")
def privacy(client):
    private_text = "PRIVATE_INSTRUCTOR_FIXTURE_DO_NOT_EXPORT"
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        result = client.create(
            response_model=User, messages=[{"role": "user", "content": private_text}]
        )
        assert result.age == 36
    finally:
        context.detach(token)
    token = context.attach(
        context.set_value(context._SUPPRESS_INSTRUMENTATION_KEY, True)
    )
    try:
        client.create(
            response_model=User,
            messages=[{"role": "user", "content": "SUPPRESSED_INSTRUCTOR_FIXTURE"}],
        )
    finally:
        context.detach(token)
    return {"privacy_checked": True}


def main():
    tracing, client = create_respan_instructor_client(app_name="instructor-privacy")
    try:
        with attributes("09_privacy.py"):
            print(privacy(client))
    finally:
        tracing.shutdown()


if __name__ == "__main__":
    main()
