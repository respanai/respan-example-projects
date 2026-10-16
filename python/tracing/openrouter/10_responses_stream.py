from _shared import MODEL, native_client, tracing, workflow


def main():
    with tracing("responses_stream"), native_client() as client:

        @workflow(name="openrouter_native_responses_stream")
        def run(prompt):
            stream = client.responses.send(model=MODEL, input=prompt, stream=True)
            with stream:
                return "".join(
                    event.delta
                    for event in stream
                    if event.type == "response.output_text.delta"
                )

        print(run("Explain trace flow briefly."))


if __name__ == "__main__":
    main()
