"""Original model/tool failures through sync and async AgentSpec paths."""

import asyncio

from _fixtures import build_agent, fixture_model
from _shared import build_respan, example_scope


async def main():
    respan = build_respan("controlled-errors")
    with example_scope("controlled-errors"):
        try:
            failures = 0
            with fixture_model():
                for asynchronous in [False, True]:
                    for tool_error in [False, True]:
                        agent = build_agent(
                            "FailureAgent", with_tool=tool_error, tool_fails=tool_error
                        )
                        request = {
                            "messages": [
                                {
                                    "role": "user",
                                    "content": "tool-call"
                                    if tool_error
                                    else "model-failure",
                                }
                            ]
                        }
                        try:
                            if asynchronous:
                                await agent.ainvoke(request)
                            else:
                                agent.invoke(request)
                        except ValueError as exc:
                            assert str(exc) == (
                                "controlled tool failure"
                                if tool_error
                                else "controlled model failure"
                            )
                            failures += 1
                        else:
                            raise AssertionError("Expected controlled failure")
            assert failures == 4
            print({"expected_failures": failures})
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
