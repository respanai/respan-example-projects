from _shared import MODEL, client, run_case


def weather(city: str) -> str:
    """Return controlled weather for a city."""
    return f"Sunny in {city}"


def action(provider):
    payload = {
        "model": MODEL,
        "message": {
            "role": "assistant",
            "content": "",
            "thinking": "Select weather tool",
            "tool_calls": [
                {"function": {"name": "weather", "arguments": {"city": "Tokyo"}}}
            ],
        },
        "done": True,
    }
    c, _, _ = client(payload)
    try:
        response = c.chat(
            model=MODEL,
            messages=[{"role": "user", "content": "Weather?"}],
            tools=[weather],
        )
        call = response.message.tool_calls[0]
        assert call.function.name == "weather"
        history = [
            {"role": "user", "content": "Weather?"},
            response.message.model_dump(exclude_none=True),
            {
                "role": "tool",
                "tool_name": "weather",
                "content": weather(**call.function.arguments),
            },
        ]
    finally:
        c._client.close()
    c, _, _ = client()
    try:
        assert c.chat(model=MODEL, messages=history).message.content
    finally:
        c._client.close()
    c, body, _ = client(frames=[payload])
    try:
        chunks = list(c.chat(model=MODEL, messages=[], tools=[weather], stream=True))
        assert len(chunks) == 1 and chunks[0].message.tool_calls
        assert body.closed
    finally:
        c._client.close()
    return (
        "native callable tool schema, historical result and current streamed tool call"
    )


if __name__ == "__main__":
    run_case("ollama_tool_calling", action)
