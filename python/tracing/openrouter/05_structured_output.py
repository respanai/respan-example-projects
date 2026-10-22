from _shared import MODEL, compatible_client, tracing, workflow
from pydantic import BaseModel


class Summary(BaseModel):
    summary: str


def main():
    with tracing("structured_parse"), compatible_client() as client:

        @workflow(name="openrouter_compatible_parse")
        def run(topic):
            response = client.chat.completions.parse(
                model=MODEL,
                messages=[{"role": "user", "content": topic}],
                response_format=Summary,
            )
            return response.choices[0].message.parsed.model_dump()

        print(run("Return a summary about observability."))


if __name__ == "__main__":
    main()
