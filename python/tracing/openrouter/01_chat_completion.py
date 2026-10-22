from _shared import MODEL, native_client, tracing, workflow


def main():
    with tracing("chat"), native_client() as client:

        @workflow(name="openrouter_native_chat")
        def run(prompt):
            response = client.chat.send(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                provider={"zdr": True, "sort": "price"},
            )
            return response.choices[0].message.content

        print(run("Reply with a sentence about observability."))


if __name__ == "__main__":
    main()
