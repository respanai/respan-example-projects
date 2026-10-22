from _shared import native_client, tracing, workflow


def main():
    with tracing("embedding"), native_client() as client:

        @workflow(name="openrouter_native_embedding")
        def run(text):
            response = client.embeddings.generate(
                model="openai/text-embedding-3-small", input=text
            )
            return {"dimensions": len(response.data[0].embedding)}

        print(run("A controlled document to embed."))


if __name__ == "__main__":
    main()
