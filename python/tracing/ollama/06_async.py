import asyncio

from _shared import CHAT, MODEL, client, run_case


async def calls():
    c, _, _ = client(asynchronous=True)
    try:
        results = await asyncio.gather(
            c.chat(model=MODEL, messages=[{"role": "user", "content": "first"}]),
            c.chat(model=MODEL, messages=[{"role": "user", "content": "second"}]),
        )
        assert all(r.message.content for r in results)
    finally:
        await c._client.aclose()
    c, body, _ = client(
        frames=[
            {
                "model": MODEL,
                "response": "Async native stream",
                "thinking": "Controlled reasoning",
                "done": True,
                "prompt_eval_count": 0,
            }
        ],
        asynchronous=True,
    )
    try:
        stream = await c.generate(model=MODEL, prompt="Async", stream=True)
        assert len([r async for r in stream]) == 1 and body.body.closed
    finally:
        await c._client.aclose()
    c, body, requests = client(frames=[CHAT], asynchronous=True)
    try:
        stream = await c.chat(model=MODEL, messages=[], stream=True)
        await stream.aclose()
        assert not requests
    finally:
        await c._client.aclose()
    c, _, _ = client(
        {"model": MODEL, "embeddings": [[0.0] * 5001], "prompt_eval_count": 0},
        asynchronous=True,
    )
    try:
        assert len((await c.embed(model=MODEL, input="")).embeddings[0]) == 5001
    finally:
        await c._client.aclose()


def action(provider):
    asyncio.run(calls())
    return "native async concurrent calls, stream, unread close and embedding"


if __name__ == "__main__":
    run_case("ollama_async", action)
