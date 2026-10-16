from _shared import MODEL, native_client, tracing, workflow
from openrouter import components


def main():
    with tracing("server_tool"), native_client() as client:

        @workflow(name="openrouter_native_server_tool")
        def run(question):
            response = client.chat.send(
                model=MODEL,
                messages=[{"role": "user", "content": question}],
                tools=[
                    components.OpenRouterWebSearchServerTool(
                        type="openrouter:web_search",
                        parameters=components.WebSearchConfig(
                            max_results=5, search_context_size="medium"
                        ),
                    )
                ],
            )
            return {"response_id": response.id}

        print(run("Search the controlled fixture for observability."))


if __name__ == "__main__":
    main()
