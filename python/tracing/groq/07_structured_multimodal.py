"""Groq 1.x JSON schema/reasoning controls and multimodal message parts."""

from _shared import make_client, model_name, run_example


def scenario():
    with make_client() as client:
        response = client.chat.completions.create(
            model=model_name(),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe the synthetic image"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://example.com/synthetic-image.png"
                            },
                        },
                    ],
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "answer",
                    "schema": {
                        "type": "object",
                        "properties": {"answer": {"type": "string"}},
                    },
                },
            },
            reasoning_effort="low",
        )
        return response.choices[0].message.content


if __name__ == "__main__":
    run_example("structured-multimodal", scenario)
