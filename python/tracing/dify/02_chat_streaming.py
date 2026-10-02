"""Streaming Dify chat message traced after stream consumption."""

from _shared import DifyExampleRuntime, collect_stream_answer, print_result


def main() -> None:
    workflow_name = "dify_chat_streaming.workflow"
    with DifyExampleRuntime(workflow_name) as runtime:
        client = runtime.chat_client()
        response = client.create_chat_message(
            inputs={},
            query="Stream a short Dify response.",
            user=runtime.user("stream"),
            response_mode="streaming",
        )
        response.raise_for_status()
        answer = collect_stream_answer(response)
        summary = {"workflow": workflow_name, "answer": answer}
        runtime.set_result(summary)
        print_result("chat_streaming", summary)


if __name__ == "__main__":
    main()
