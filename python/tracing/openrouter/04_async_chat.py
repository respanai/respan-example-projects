import asyncio

from _shared import MODEL, native_client, tracing, workflow


async def main():
    with tracing("async_chat"):
        async with native_client(asynchronous=True) as client:

            @workflow(name="openrouter_native_async_chat")
            async def run(prompt):
                response = await client.chat.send_async(
                    model=MODEL, messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content

            print(await run("Describe one benefit of tracing."))


if __name__ == "__main__":
    asyncio.run(main())
