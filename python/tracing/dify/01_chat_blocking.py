"""Blocking Dify chat message traced by Respan."""

from _shared import DifyExampleRuntime, print_result


def main() -> None:
    workflow_name = "dify_chat_blocking.workflow"
    with DifyExampleRuntime(workflow_name) as runtime:
        client = runtime.chat_client()
        user = runtime.user("chat")
        response = client.create_chat_message(
            inputs={"city": "Paris"},
            query="Reply with one sentence about observability.",
            user=user,
            response_mode="blocking",
        )
        response.raise_for_status()
        result = response.json()
        summary = {"workflow": workflow_name, "answer": result.get("answer")}
        runtime.set_result(summary)
        print_result("chat_blocking", summary)


if __name__ == "__main__":
    main()
