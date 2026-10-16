from _shared import MODEL, native_client, tracing, workflow


def main():
    with tracing("responses"), native_client() as client:

        @workflow(name="openrouter_native_responses")
        def run(prompt):
            response = client.responses.send(model=MODEL, input=prompt)
            beta = client.beta.responses.send(model=MODEL, input=prompt)
            return {
                "stable": response.output[0].content[0].text,
                "beta": beta.output[0].content[0].text,
            }

        print(run("Reply with a sentence about tracing."))


if __name__ == "__main__":
    main()
