"""Native raw responses and lazy HTTP response context managers."""

from _shared import make_client, model_name, run_example


def scenario():
    with make_client() as client:
        parameters = {
            "model": model_name(),
            "messages": [{"role": "user", "content": "Synthetic raw response"}],
        }
        response = client.chat.completions.with_raw_response.create(
            **parameters, stream=True
        )
        stream = response.parse()
        assert stream is response.parse()
        list(stream)
        response.close()
        with client.chat.completions.with_streaming_response.create(
            **parameters
        ) as response:
            response.parse()
        return {"raw_status": response.status_code}


if __name__ == "__main__":
    run_example("response-helpers", scenario)
