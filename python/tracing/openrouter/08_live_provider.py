import os

from _shared import MODEL, native_client, tracing, workflow


def main():
    if os.getenv("OPENROUTER_EXAMPLE_LIVE") != "1":
        print("Live provider example skipped; set OPENROUTER_EXAMPLE_LIVE=1 to opt in.")
        return
    with tracing("live_chat"), native_client(live=True) as client:

        @workflow(name="openrouter_native_live")
        def run(prompt):
            response = client.chat.send(
                model=os.getenv("OPENROUTER_MODEL", MODEL),
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

        print(run("Reply with one concise sentence about observability."))


if __name__ == "__main__":
    main()
