"""Dify workflow, parameters, conversations, messages, and feedback tracing."""

import inspect

from _shared import DifyExampleRuntime, print_result


def main() -> None:
    workflow_name = "dify_workflow_and_api.workflow"
    with DifyExampleRuntime(workflow_name) as runtime:
        raw_client = runtime.raw_client()
        chat_client = runtime.chat_client()
        workflow_client = runtime.workflow_client()
        user = runtime.user("api")

        if workflow_client is not None:
            workflow_response = workflow_client.run(
                inputs={"query": "Summarize Dify tracing."},
                response_mode="blocking",
                user=user,
            )
        else:
            workflow_response = raw_client._send_request(
                "POST",
                "/workflows/run",
                json={
                    "inputs": {"query": "Summarize Dify tracing."},
                    "response_mode": "blocking",
                    "user": user,
                },
            )
        workflow_response.raise_for_status()

        parameters = chat_client.get_application_parameters(user=user)
        parameters.raise_for_status()
        conversations = chat_client.get_conversations(user=user)
        conversations.raise_for_status()
        messages = chat_client.get_conversation_messages(
            user=user,
            conversation_id="conv-local-001",
        )
        messages.raise_for_status()
        feedback = raw_client.message_feedback(
            message_id="msg-local-001",
            rating="like",
            user=user,
        )
        feedback.raise_for_status()
        rename_kwargs = {
            "conversation_id": "conv-local-001",
            "name": "Renamed local conversation",
            "user": user,
        }
        if (
            "auto_generate"
            in inspect.signature(chat_client.rename_conversation).parameters
        ):
            rename_kwargs["auto_generate"] = False
        rename = chat_client.rename_conversation(**rename_kwargs)
        rename.raise_for_status()

        summary = {
            "workflow": workflow_name,
            "workflow_run_id": workflow_response.json().get("workflow_run_id"),
            "parameters_keys": sorted(parameters.json().keys()),
            "conversations": len(conversations.json().get("data", [])),
            "messages": len(messages.json().get("data", [])),
            "feedback": feedback.json().get("result"),
            "rename": rename.json().get("result"),
        }
        runtime.set_result(summary)
        print_result("workflow_and_api", summary)


if __name__ == "__main__":
    main()
