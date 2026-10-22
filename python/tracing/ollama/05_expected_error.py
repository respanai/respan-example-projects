import ollama
from _shared import CHAT, MODEL, client, run_case


def action(provider):
    c, _, _ = client({"error": "Controlled provider refusal"}, status=429)
    try:
        try:
            c.chat(model=MODEL, messages=[])
        except ollama.ResponseError as error:
            assert error.status_code == 429
        else:
            raise AssertionError("expected native provider error")
    finally:
        c._client.close()
    c, body, _ = client(frames=[CHAT, {"error": "Controlled stream failure"}])
    try:
        try:
            list(c.chat(model=MODEL, messages=[], stream=True))
        except ollama.ResponseError as error:
            assert error.status_code == -1 and body.closed
        else:
            raise AssertionError("expected native event error")
    finally:
        c._client.close()
    c, _, _ = client({"response": ""})
    try:
        assert c.generate(model=MODEL, prompt="").response == ""
    finally:
        c._client.close()
    return "native HTTP 429, HTTP 200 event failure with partial output, and empty generation response"


if __name__ == "__main__":
    run_case("ollama_expected_error", action)
