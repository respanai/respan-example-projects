"""Dify file upload plus Respan propagated attributes."""

from _shared import DifyExampleRuntime, print_result, sample_file


def main() -> None:
    workflow_name = "dify_context_and_files.workflow"
    with DifyExampleRuntime(workflow_name) as runtime:
        raw_client = runtime.raw_client()
        chat_client = runtime.chat_client()
        user = runtime.user("context")

        with runtime.respan.propagate_attributes(
            customer_identifier=user,
            thread_identifier="dify-thread-context",
            trace_group_identifier=workflow_name,
            metadata={"example": "dify_context_and_files", "tier": "demo"},
        ):
            with sample_file() as file_obj:
                upload = raw_client.file_upload(
                    user=user,
                    files={"file": ("sample.txt", file_obj, "text/plain")},
                )
            upload.raise_for_status()
            upload_id = upload.json().get("id")

            response = chat_client.create_chat_message(
                inputs={},
                query="Describe the uploaded file purpose in one sentence.",
                user=user,
                response_mode="blocking",
                files=[
                    {
                        "type": "document",
                        "transfer_method": "local_file",
                        "upload_file_id": upload_id,
                    }
                ],
                respan_params={
                    "span_name": "dify.context.chat",
                    "workflow_name": workflow_name,
                    "metadata": {"request_kind": "file_chat"},
                },
            )
            response.raise_for_status()

        summary = {
            "workflow": workflow_name,
            "upload_id": upload_id,
            "answer": response.json().get("answer"),
        }
        runtime.set_result(summary)
        print_result("context_and_files", summary)


if __name__ == "__main__":
    main()
