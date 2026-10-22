from _shared import GEN, close, native, run_case
from ibm_watsonx_ai.wml_client_error import WMLClientError


def action(provider):
    c, m, *_ = native(
        {"errors": [{"code": "controlled_limit", "message": "Controlled refusal."}]},
        status=429,
    )
    try:
        try:
            m.generate(prompt="Controlled expected HTTP error.")
        except WMLClientError:
            pass
        else:
            raise AssertionError("native HTTP error missing")
    finally:
        close(c)
    c, m, _e, _requests, _responses, body, *_ = native(
        frames=[
            GEN,
            b'event: error\ndata: {"message":"Controlled stream refusal."}\n\n',
        ]
    )
    try:
        s = m.generate_text_stream(
            prompt="Controlled partial SSE error.", raw_response=True
        )
        assert next(s) == GEN
        try:
            next(s)
        except WMLClientError:
            pass
        else:
            raise AssertionError("native SSE error missing")
        assert body.closed == 1
    finally:
        close(c)
    return "native HTTP 429 and partial SSE failure"


if __name__ == "__main__":
    run_case("watsonx_expected_errors", action)
