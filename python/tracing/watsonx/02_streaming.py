from _shared import GEN, close, native, run_case


def action(provider):
    frames = [
        {
            "model_id": "reported-granite",
            "results": [
                {
                    "generated_text": str(n) + " ",
                    "input_token_count": 0,
                    "generated_token_count": 0,
                }
            ],
        }
        for n in range(300)
    ]
    c, m, _e, requests, _responses, body, *_ = native(frames=frames)
    try:
        s = m.generate_text_stream(prompt="Controlled full stream.")
        assert not requests and not body.reads
        assert len(list(s)) == 300 and body.closed == 1
    finally:
        close(c)
    pieces = [
        {
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call-stream",
                                "type": "function",
                                "function": {"name": "get_weather", "arguments": piece},
                            }
                        ],
                    },
                }
            ]
        }
        for piece in ('{"city":', '"Tokyo"}')
    ]
    c, m, _e, requests, _responses, body, *_ = native(frames=pieces)
    try:
        assert list(m.chat_stream(messages=[])) == pieces and body.closed == 1
    finally:
        close(c)
    c, m, _e, requests, _responses, body, *_ = native(frames=[GEN, GEN])
    try:
        s = m.generate_text_stream(
            prompt="Controlled partial stream.", raw_response=True
        )
        assert next(s) == GEN
        s.close()
        assert body.closed == 1
        s = m.generate_text_stream(prompt="Controlled unopened stream.")
        s.close()
        assert len(requests) == 1
    finally:
        close(c)
    return "300 native SSE frames, fragmented tool calls, partial and unopened close"


if __name__ == "__main__":
    run_case("watsonx_streams", action)
