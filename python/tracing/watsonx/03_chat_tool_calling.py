from _shared import CHAT, close, native, run_case
from ibm_watsonx_ai.foundation_models.schema import TextChatParameters


def action(provider):
    history = [
        {"role": "user", "content": f"Controlled history {n}"} for n in range(75)
    ]
    history[0] = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "historical-call",
                "type": "function",
                "function": {"name": "get_weather", "arguments": "{}"},
            }
        ],
    }
    schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "api_key": {"type": "string", "example": "controlled-secret"},
        },
        "required": ["city"],
    }
    tools = [
        {"type": "function", "function": {"name": "get_weather", "parameters": schema}}
    ]
    c, m, *_ = native(CHAT)
    try:
        result = m.chat(
            messages=history,
            tools=tools,
            tool_choice_option="auto",
            params=TextChatParameters(
                temperature=0, max_tokens=0, response_format={"type": "json_object"}
            ),
        )
        call = result["choices"][0]["message"]["tool_calls"][0]
        followup = history + [
            result["choices"][0]["message"],
            {
                "role": "tool",
                "tool_call_id": call["id"],
                "content": "Controlled Tokyo weather: sunny.",
            },
        ]
        m.chat(messages=followup, tools=tools)
    finally:
        close(c)
    blocked = {
        "model_id": "reported-granite",
        "choices": [],
        "prompt_feedback": {"block_reason": "SAFETY"},
        "custom": {"flag": False},
    }
    c, m, *_ = native(blocked)
    try:
        assert m.chat(messages=[]) == blocked
    finally:
        close(c)
    return "full history/settings/schema, historical/current IDs, native empty feedback"


if __name__ == "__main__":
    run_case("watsonx_chat_tools", action)
