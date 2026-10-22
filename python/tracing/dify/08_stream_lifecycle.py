"""Early stream close and Dify protocol failures using the local fixture server."""

from _shared import DifyExampleRuntime


def main():
    with DifyExampleRuntime("dify_stream_lifecycle.workflow") as runtime:
        if not runtime.is_local:
            runtime.set_result(
                {"status": "skipped", "reason": "requires fixture server"}
            )
            return
        client = runtime.chat_client()
        response = client.create_chat_message(
            inputs={},
            query="partial stream",
            user="fixture-user",
            response_mode="streaming",
        )
        iterator = response.iter_lines()
        assert next(iterator)
        response.close()
        iterator.close()
        failed = client.create_chat_message(
            inputs={},
            query="controlled SSE failure",
            user="fixture-user",
            response_mode="streaming",
        )
        assert list(failed.iter_lines())
        failed.close()
        workflow = client._send_request(
            "POST",
            "/workflows/run",
            json={
                "inputs": {"query": "controlled workflow failure"},
                "response_mode": "blocking",
            },
        )
        assert workflow.json()["data"]["status"] == "failed"
        close = getattr(client, "close", None)
        if close:
            close()
        runtime.set_result({"partial_closed": True, "controlled_errors": 2})


if __name__ == "__main__":
    main()
