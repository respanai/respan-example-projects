import asyncio

from _shared import MODEL, native_client, tracing, workflow


async def main():
    with tracing("async_responses_embedding"):
        async with native_client(asynchronous=True) as client:

            @workflow(name="openrouter_native_async_responses_embedding")
            async def run(prompt):
                regular = await client.responses.send_async(model=MODEL, input=prompt)
                stream = await client.responses.send_async(
                    model=MODEL, input=prompt, stream=True
                )
                async with stream:
                    text = "".join(
                        [
                            event.delta
                            async for event in stream
                            if event.type == "response.output_text.delta"
                        ]
                    )
                embedding = await client.embeddings.generate_async(
                    model="openai/text-embedding-3-small", input=prompt
                )
                return {
                    "regular_text": regular.output[0].content[0].text,
                    "text": text,
                    "dimensions": len(embedding.data[0].embedding),
                }

            print(await run("A bounded async fixture input."))


if __name__ == "__main__":
    asyncio.run(main())
