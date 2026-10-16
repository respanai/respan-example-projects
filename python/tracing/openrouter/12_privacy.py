import os

from _shared import MODEL, native_client, tracing, workflow


def main():
    os.environ["TRACELOOP_TRACE_CONTENT"] = "off"
    with tracing("privacy") as memory:
        with native_client() as client:

            @workflow(name="openrouter_native_private")
            def run(prompt):
                response = client.chat.send(
                    model=MODEL, messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content

            run("PRIVATE input must never be exported.")
        span = next(
            s for s in memory.get_finished_spans() if s.name == "openrouter.chat"
        )
        assert "traceloop.entity.input" not in span.attributes
        assert "traceloop.entity.output" not in span.attributes
    print("Content opt-out verified.")


if __name__ == "__main__":
    main()
