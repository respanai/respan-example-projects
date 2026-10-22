import asyncio

from _shared import EMB, close, native, run_case


async def async_calls():
    c, _m, e, *_ = native(EMB)
    try:
        assert (
            len((await e.agenerate(inputs=["Controlled"]))["results"][0]["embedding"])
            == 5001
        )
        assert len((await e.aembed_documents(["Controlled"]))[0]) == 5001
        assert len(await e.aembed_query("Controlled")) == 5001
    finally:
        await c.async_httpx_client.aclose()
        close(c)


def action(provider):
    c, _m, e, *_ = native(EMB)
    try:
        assert len(e.generate(inputs=["one", "two", "three", "four"])["results"]) == 2
        assert len(e.embed_documents(["Controlled"])[0]) == 5001
        assert len(e.embed_query("Controlled")) == 5001
    finally:
        close(c)
    asyncio.run(async_calls())
    return "six native embedding methods, batches and full 5001 vectors"


if __name__ == "__main__":
    run_case("watsonx_embeddings", action)
