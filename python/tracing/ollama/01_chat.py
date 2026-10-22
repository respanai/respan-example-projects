import ollama
from _shared import CHAT, MODEL, client, run_case


def action(provider):
    c, _, requests = client()
    try:
        history = [
            {"role": "user", "content": f"Controlled history {i}"} for i in range(75)
        ]
        history[-1]["images"] = [b"controlled-image"]
        schema = {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "default": "controlled-secret"},
                "answer": {"type": "string"},
            },
        }
        response = c.chat(
            model=MODEL,
            messages=history,
            format=schema,
            options=ollama.Options(temperature=0, num_predict=0, seed=0),
            think=False,
            keep_alive=0,
        )
        assert (
            response.message.thinking == CHAT["message"]["thinking"]
            and len(requests) == 1
        )
        return "75 native messages, image, structured format and zero settings"
    finally:
        c._client.close()


if __name__ == "__main__":
    run_case("ollama_chat_settings", action)
