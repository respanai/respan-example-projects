from _shared import native_client, tracing, workflow
from openrouter.errors import OpenRouterError


def main():
    with tracing("provider_error"), native_client() as client:

        @workflow(name="openrouter_native_error")
        def run(trigger_prompt):
            try:
                client.chat.send(
                    model="fixture/error",
                    messages=[{"role": "user", "content": trigger_prompt}],
                )
            except OpenRouterError as error:
                assert error.status_code == 429
                return {"expected_error": type(error).__name__}
            raise AssertionError("The fixture must raise a provider error")

        print(run("Trigger the controlled rate limit."))


if __name__ == "__main__":
    main()
