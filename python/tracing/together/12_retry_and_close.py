from _fixtures import NativeRuntime
from _shared import create_respan, example_attributes, finish_respan
from respan import workflow


def main():
    runtime = NativeRuntime()
    runtime.retry = True
    respan = create_respan()

    @workflow(name="together_retry_close")
    def invoke(prompt):
        with runtime.client(retries=1) as client:
            native = client.chat.completions.create(
                model="native-model", messages=[{"role": "user", "content": prompt}]
            )
            assert runtime.attempts == runtime.callback_count == 2
            partial = client.chat.completions.create(
                model="native-model",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            with partial as entered:
                assert entered is partial
                next(partial)
            unread = client.chat.completions.create(
                model="native-model",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            unread.close()
            return native.choices[0].message.content

    try:
        with example_attributes("retry-close"):
            assert invoke("controlled") == "native response"
        print("retry-close: native retries/callbacks/contextmanager and original close")
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
