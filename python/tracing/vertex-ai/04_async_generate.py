import asyncio

from _fixtures import NativeRuntime
from _shared import create_respan, example_context, finish_respan
from respan import workflow


async def main():
    native = NativeRuntime()
    respan = create_respan()
    model, channel = await native.async_model()

    @workflow(name="vertexai_async")
    async def generate(prompt):
        assert (await model.generate_content_async(prompt)).text == "native response"
        chat = model.start_chat()
        assert (await chat.send_message_async(prompt)).text == "native response"
        stream = await model.generate_content_async(prompt, stream=True)
        chunks = [chunk async for chunk in stream]
        assert len(chunks) == 70
        partial = await model.generate_content_async(prompt, stream=True)
        await partial.__anext__()
        await partial.aclose()
        unread = await model.generate_content_async(prompt, stream=True)
        await unread.aclose()
        return "".join(chunk.text for chunk in chunks)

    try:
        with example_context("async"):
            assert (await generate("hello")).endswith("69,")
        print("async: generation/chat/70-chunk stream and aclose preserved")
    finally:
        await channel.close()
        native.close()
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
