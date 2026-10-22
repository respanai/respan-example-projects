from __future__ import annotations

from _shared import clients, example_attributes, finish, make_respan
from respan import workflow

EXAMPLE = "core"


@workflow(name="exa_python_core")
def core_calls(client):
    search = client.search(
        "recent retrieval instrumentation developments",
        type="auto",
        num_results=1,
        contents={"highlights": True},
    )
    contents = client.get_contents(
        ["https://example.com/article"],
        text={"max_characters": 1000},
    )
    answer = client.answer(
        "What does the loopback source say?",
        system_prompt="Answer concisely and cite the source.",
    )
    return {
        "search_title": search.results[0].title,
        "contents_text": contents.results[0].text,
        "answer": answer.answer,
    }


def main() -> None:
    respan = make_respan(EXAMPLE)
    try:
        with (
            clients() as (client, _async_client, mode),
            example_attributes(EXAMPLE, mode) as workflow_name,
        ):
            result = core_calls(client)
            print({"workflow_name": workflow_name, "mode": mode, **result})
    finally:
        finish(respan)


if __name__ == "__main__":
    main()
