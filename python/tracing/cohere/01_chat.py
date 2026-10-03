from _shared import (
    CHAT_MODEL,
    create_cohere_client,
    create_respan,
    install_cohere_stubs_if_needed,
    run_with_example_attributes,
)
from respan import workflow

WORKFLOW_NAME = "cohere_chat.workflow"

install_cohere_stubs_if_needed()
respan = create_respan("cohere-chat-example")
client = create_cohere_client()


@workflow(name=WORKFLOW_NAME)
def cohere_chat() -> str:
    response = client.chat(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "user",
                "content": "In one sentence, describe what Cohere rerank is useful for.",
            }
        ],
        temperature=0.1,
        max_tokens=80,
    )
    return response.message.content[0].text


def main() -> None:
    try:
        output = run_with_example_attributes(
            respan,
            workflow_name=WORKFLOW_NAME,
            action=cohere_chat,
        )
        print(output)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
