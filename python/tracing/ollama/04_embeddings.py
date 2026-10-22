from _shared import MODEL, client, run_case


def action(provider):
    c, _, _ = client(
        {
            "model": MODEL,
            "embeddings": [[0.0] * 5001, [1.0] * 5001],
            "prompt_eval_count": 0,
            "total_duration": 0,
            "custom": {"flag": False, "api_key": "controlled-secret"},
        }
    )
    try:
        response = c.embed(
            model=MODEL,
            input=["", "Controlled embedding"],
            dimensions=5001,
            truncate=False,
            options={"temperature": 0},
            keep_alive=0,
        )
        assert len(response.embeddings) == 2 and len(response.embeddings[0]) == 5001
    finally:
        c._client.close()
    c, _, _ = client({"embedding": [0.0] * 5001})
    try:
        assert (
            len(
                c.embeddings(
                    model=MODEL, prompt="", options={"seed": 0}, keep_alive=0
                ).embedding
            )
            == 5001
        )
    finally:
        c._client.close()
    return (
        "native batch and legacy 5001-dimensional vectors, zero usage and empty input"
    )


if __name__ == "__main__":
    run_case("ollama_embeddings", action)
