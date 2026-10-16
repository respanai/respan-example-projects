"""Run separately in either supported legacy extra environment; no provider call."""

import os

from _shared import run

from autogen import ConversableAgent


async def scenario():
    def agent(name, **kwargs):
        return ConversableAgent(
            name,
            llm_config=False,
            human_input_mode="NEVER",
            code_execution_config=False,
            max_consecutive_auto_reply=1,
            **kwargs,
        )

    sender = agent("sender", default_auto_reply="Sender fixture.")
    receiver = agent("receiver", default_auto_reply="Receiver fixture.")
    sender.initiate_chat(receiver, message="Legacy synchronous fixture.", silent=True)
    await sender.a_initiate_chat(
        receiver, message="Legacy asynchronous fixture.", silent=True
    )

    def fail():
        raise ValueError("Controlled legacy tool failure")

    executor = agent("executor", function_map={"zero": lambda: 0, "fail": fail})
    assert executor.execute_function({"name": "zero", "arguments": "{}"})[1][
        "content"
    ] in (0, "0")
    assert executor.execute_function({"name": "fail", "arguments": "{}"})[0] is False
    return "Legacy sync/async chat, zero tool and error verified."


if __name__ == "__main__":
    run(
        "legacy-" + os.getenv("RESPAN_LEGACY_FAMILY", "fixture"), scenario, api="legacy"
    )
