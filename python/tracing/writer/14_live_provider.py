import os

from _shared import example_attributes, finish_respan, make_client, make_respan


def run():
    if os.getenv("WRITER_EXAMPLE_LIVE") != "1":
        print("live-provider: skipped (set WRITER_EXAMPLE_LIVE=1)")
        return
    if not os.getenv("WRITER_MODEL"):
        raise RuntimeError("Set WRITER_MODEL for the explicit live call")
    os.environ["WRITER_EXAMPLE_MODE"] = "live"
    respan = make_respan("live-provider")
    try:
        with example_attributes("live-provider"), make_client() as client:
            result = client.chat.chat(
                model=os.environ["WRITER_MODEL"],
                messages=[{"role": "user", "content": "Say hello."}],
                max_tokens=32,
            )
            print(result.choices[0].message.content)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run()
