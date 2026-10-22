from __future__ import annotations

from _shared import clients, example_attributes, finish, make_respan, use_live_exa
from respan import workflow

EXAMPLE = "agent-research-tools"


@workflow(name="exa_python_agent_research_tools")
def agent_research_tools(client):
    search_tool = client.tools.web_search(num_results=1)
    tool_output = search_tool.run({"query": "latest retrieval observability patterns"})
    contents_tool = client.tools.get_contents(text={"max_characters": 500})
    contents_output = contents_tool.run({"urls": ["https://example.com/article"]})

    agent = client.agent.runs.create_and_wait(
        query="Create a one-line brief about retrieval observability.",
        poll_interval=50,
        timeout_ms=120000,
    )

    research_status = "skipped-live-deprecated"
    research_output = None
    if not use_live_exa():
        research = client.research.create(
            instructions="Create a deterministic research brief.",
            model="exa-research-fast",
        )
        completed = client.research.poll_until_finished(
            research.research_id,
            poll_interval=50,
            timeout_ms=10000,
        )
        research_status = completed.status
        research_output = completed.output.content if completed.output else None

    return {
        "tool_output": tool_output,
        "contents_output": contents_output,
        "agent_status": agent.status,
        "agent_output": agent.output.text if agent.output else None,
        "research_status": research_status,
        "research_output": research_output,
    }


def main() -> None:
    respan = make_respan(EXAMPLE)
    try:
        with (
            clients() as (client, _async_client, mode),
            example_attributes(EXAMPLE, mode) as workflow_name,
        ):
            result = agent_research_tools(client)
            print({"workflow_name": workflow_name, "mode": mode, **result})
    finally:
        finish(respan)


if __name__ == "__main__":
    main()
