import asyncio

from _shared import CHAT, GEN, close, native, run_case


async def calls():
    for method, payload, frames in [
        ("agenerate", GEN, None),
        ("achat", CHAT, None),
        ("agenerate_stream", GEN, [GEN]),
        ("achat_stream", CHAT, [CHAT]),
    ]:
        c, m, _e, _requests, _responses, _b, ab = native(payload, frames=frames)
        try:
            r = (
                await getattr(m, method)(messages=[] if "chat" in method else None)
                if "chat" in method
                else await getattr(m, method)(prompt="Controlled async.")
            )
            if frames is not None:
                assert [item async for item in r] == frames and ab.body.closed == 1
            else:
                assert r == payload
        finally:
            await c.async_httpx_client.aclose()
            close(c)
    return "all four native async model methods"


def action(provider):
    return asyncio.run(calls())


if __name__ == "__main__":
    run_case("watsonx_async_models", action)
