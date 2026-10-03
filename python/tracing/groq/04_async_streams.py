"""Async chat, fragmented tool calls and explicit early close."""

from _shared import make_async_client, model_name, run_example


async def scenario():
    async with make_async_client() as client:
        messages = [{"role": "user", "content": "Synthetic async hello"}]
        await client.chat.completions.create(model=model_name(), messages=messages)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "parameters": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                    },
                },
            }
        ]
        stream = await client.chat.completions.create(
            model=model_name(), messages=messages, tools=tools, stream=True
        )
        chunks = [chunk async for chunk in stream]
        await stream.close()
        partial = await client.chat.completions.create(
            model=model_name(), messages=messages, stream=True
        )
        await anext(partial)
        await partial.close()
        return {"stream_chunks": len(chunks), "partial_closed": True}


if __name__ == "__main__":
    run_example("async-streams", scenario)
