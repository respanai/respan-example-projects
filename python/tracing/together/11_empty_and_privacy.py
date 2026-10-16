from _fixtures import NativeRuntime
from _shared import create_respan, example_attributes, finish_respan
from opentelemetry import context
from respan import workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def main():
    runtime = NativeRuntime()
    respan = create_respan()

    @workflow(name="together_empty_private")
    def invoke(prompt):
        with runtime.client() as client:
            return client.chat.completions.create(
                model="native-model", messages=[{"role": "user", "content": prompt}]
            )

    try:
        with example_attributes("empty-privacy"):
            assert invoke("empty").choices == []
            token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
            try:
                assert invoke("private").choices[0].message.content == "native response"
            finally:
                context.detach(token)
            with runtime.client() as client:
                source = client.chat.completions.create(
                    model="native-model",
                    messages=[{"role": "user", "content": "late-private"}],
                    stream=True,
                )
                next(source)
                token = context.attach(
                    context.set_value(ENABLE_CONTENT_TRACING_KEY, False)
                )
                context.detach(token)
                source.close()
        print("empty-privacy: full native empty feedback and irreversible veto")
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
