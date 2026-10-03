from _shared import (
    CHAT_MODEL,
    create_cohere_client,
    create_respan,
    install_cohere_stubs_if_needed,
    run_with_example_attributes,
)
from respan import workflow

WORKFLOW_NAME = "cohere_streaming_chat.workflow"

install_cohere_stubs_if_needed()
respan = create_respan("cohere-streaming-chat-example")
client = create_cohere_client()


@workflow(name=WORKFLOW_NAME)
def cohere_streaming_chat() -> str:
    chunks: list[str] = []
    stream = client.chat_stream(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "user",
                "content": "Write a short status update for a Cohere tracing demo.",
            }
        ],
        temperature=0.1,
        max_tokens=80,
    )
    for event in stream:
        if event.type == "content-delta":
            chunks.append(event.delta.message.content.text)
    return "".join(chunks)


def main() -> None:
    try:
        output = run_with_example_attributes(
            respan,
            workflow_name=WORKFLOW_NAME,
            action=cohere_streaming_chat,
        )
        print(output)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
