from _shared import MODEL, native_client, tracing, workflow


def main():
    with tracing("chat_stream"), native_client() as client:

        @workflow(name="openrouter_native_chat_stream")
        def run(prompt):
            stream = client.chat.send(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            with stream:
                return "".join(
                    chunk.choices[0].delta.content or ""
                    for chunk in stream
                    if chunk.choices
                )

        print(run("Explain trace flow briefly."))


if __name__ == "__main__":
    main()
