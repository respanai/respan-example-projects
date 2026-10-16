"""Disable Dify content while retaining source model and usage fields."""

from _shared import DifyExampleRuntime
from opentelemetry import context
from opentelemetry.context import _SUPPRESS_INSTRUMENTATION_KEY


def main():
    with DifyExampleRuntime(
        "dify_content_opt_out.workflow", include_content=False
    ) as runtime:
        client = runtime.chat_client()
        response = client.create_chat_message(
            inputs={},
            query="private fixture prompt",
            user="fixture-user",
            response_mode="blocking",
        )
        response.raise_for_status()
        assert response.json()["answer"]
        token = context.attach(context.set_value(_SUPPRESS_INSTRUMENTATION_KEY, True))
        try:
            suppressed = client.create_chat_message(
                inputs={},
                query="private suppressed fixture",
                user="fixture-user",
                response_mode="blocking",
            )
            suppressed.raise_for_status()
        finally:
            context.detach(token)
        close = getattr(client, "close", None)
        if close:
            close()
        runtime.set_result(
            {"content_capture": False, "suppressed_call_completed": True}
        )


if __name__ == "__main__":
    main()
