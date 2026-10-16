"""Concurrent async AgentSpec agents and a separate async tool call."""

import asyncio

from _fixtures import build_agent, fixture_model
from _shared import build_respan, example_scope, latest_message_content


async def main():
    respan = build_respan("async-agents")
    with example_scope("async-agents"):
        try:
            with fixture_model():
                results = await asyncio.gather(
                    *(
                        build_agent("Agent-" + p).ainvoke(
                            {"messages": [{"role": "user", "content": p}]}
                        )
                        for p in ["alpha", "beta"]
                    )
                )
                tool = await build_agent("AsyncCalculator", with_tool=True).ainvoke(
                    {"messages": [{"role": "user", "content": "tool-call"}]}
                )
            assert [latest_message_content(result) for result in results] == [
                "answer alpha",
                "answer beta",
            ]
            assert latest_message_content(tool) == "0.0"
            print({"agents": 2, "tool_result": latest_message_content(tool)})
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
