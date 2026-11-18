from _fixtures import NativeRuntime
from _shared import create_respan, example_context, finish_respan
from opentelemetry import context
from respan import workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


def main():
    native = NativeRuntime()
    respan = create_respan()

    @workflow(name="vertexai_private")
    def generate(prompt):
        return native.model().generate_content(prompt).text

    try:
        with example_context("privacy"):
            token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
            try:
                assert generate("private controlled prompt") == "native response"
            finally:
                context.detach(token)
            source = native.model().generate_content(
                "late private controlled prompt", stream=True
            )
            next(source)
            token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
            try:
                next(source)
            finally:
                context.detach(token)
            source.close()
        print("privacy: initial and irreversible late veto preserve native results")
    finally:
        native.close()
        finish_respan(respan)


if __name__ == "__main__":
    main()
