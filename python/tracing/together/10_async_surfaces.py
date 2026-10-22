import asyncio

from _fixtures import NativeRuntime
from _shared import create_respan, example_attributes, finish_respan
from respan import workflow


async def main():
    runtime = NativeRuntime()
    respan = create_respan()

    @workflow(name="together_async_surfaces")
    async def invoke(prompt):
        async with runtime.async_client() as client:
            response = await client.completions.create(
                model="native-model", prompt=prompt
            )
            assert response.choices[0].text == "native completion"
            source = await client.chat.completions.create(
                model="native-model",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            chunks = [chunk async for chunk in source]
            assert len(chunks) == 70 and source.response.is_closed
            unread = await client.chat.completions.create(
                model="native-model",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            await unread.close()
            embed = await client.embeddings.create(
                model="native-embedding", input=[prompt]
            )
            assert len(embed.data[0].embedding) == 5001
            await client.rerank.create(
                model="native-rerank", query=prompt, documents=["first", "second"]
            )
            image = await client.images.generate(
                model="native-image", prompt=prompt, response_format="b64_json"
            )
            assert image.data[0].b64_json == "Y29udHJvbGxlZA=="
            return {"chunks": len(chunks), "dimensions": len(embed.data[0].embedding)}

    try:
        with example_attributes("async-surfaces"):
            await invoke("controlled")
        print("async-surfaces: all native operations,70chunks and unread close")
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
