from _fixtures import NativeRuntime
from _shared import create_respan, example_context, finish_respan
from google.api_core.exceptions import ServiceUnavailable
from respan import workflow


def main():
    native = NativeRuntime()
    respan = create_respan()

    @workflow(name="vertexai_error")
    def generate(prompt):
        return native.model().generate_content(prompt)

    try:
        with example_context("expected-error"):
            try:
                generate("failure")
            except ServiceUnavailable as error:
                assert error.code == 503
            else:
                raise AssertionError("expected native Google error")
            blocked = generate("blocked")
            assert (
                not blocked.candidates
                and blocked._raw_response.prompt_feedback.block_reason
            )
        print("expected-error: native ServiceUnavailable preserved")
    finally:
        native.close()
        finish_respan(respan)


if __name__ == "__main__":
    main()
