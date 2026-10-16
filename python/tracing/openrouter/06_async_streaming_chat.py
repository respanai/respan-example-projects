import asyncio

from _shared import MODEL, native_client, tracing, workflow


async def main():
    with tracing("async_chat_stream"):
        async with native_client(asynchronous=True) as client:

            @workflow(name="openrouter_native_async_stream")
            async def run(prompt):
                stream = await client.chat.send_async(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                )
                parts = []
                async with stream:
                    async for chunk in stream:
                        if chunk.choices:
                            parts.append(chunk.choices[0].delta.content or "")
                return "".join(parts)

            print(await run("Explain trace flow briefly."))


if __name__ == "__main__":
    asyncio.run(main())
