from _shared import MODEL, client, run_case


def action(provider):
    frames = [
        {"model": MODEL, "response": "x" * 10000, "thinking": "r" * 10000},
        {
            "model": MODEL,
            "response": "",
            "done": True,
            "prompt_eval_count": 0,
            "eval_count": 0,
            "prompt_eval_cached_count": 0,
        },
    ]
    c, body, _ = client(frames=frames)
    try:
        chunks = list(
            c.generate(
                model=MODEL,
                prompt="Controlled stream",
                system="",
                context=[],
                raw=False,
                think=True,
                stream=True,
            )
        )
        assert (
            len("".join(chunk.response or "" for chunk in chunks)) == 10000
            and body.closed
        )
    finally:
        c._client.close()
    c, body, _ = client(frames=frames)
    try:
        stream = c.generate(model=MODEL, prompt="Partial stream", stream=True)
        next(stream)
        stream.close()
        assert body.closed
    finally:
        c._client.close()
    c, body, requests = client(frames=frames)
    try:
        stream = c.generate(model=MODEL, prompt="Unread stream", stream=True)
        stream.close()
        assert not requests and not body.reads
    finally:
        c._client.close()
    return "full reasoning stream, partial close and pre-first close"


if __name__ == "__main__":
    run_case("ollama_stream_generate", action)
