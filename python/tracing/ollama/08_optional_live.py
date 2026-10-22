"""A real local Ollama server/model is used only with explicit live opt-in."""

import os

import ollama
from _shared import run_case


def action(provider):
    c = ollama.Client(host=os.getenv("OLLAMA_HOST"))
    try:
        response = c.chat(
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            messages=[
                {"role": "user", "content": "Reply with one concise tracing sentence."}
            ],
        )
        assert response.message.content
        return "real local Ollama response received"
    finally:
        c._client.close()


if __name__ == "__main__":
    if os.getenv("RESPAN_OLLAMA_LIVE") == "1":
        run_case("ollama_optional_live", action)
    else:
        print(
            "SKIP optional live: set RESPAN_OLLAMA_LIVE=1 and install a model on your Ollama server"
        )
