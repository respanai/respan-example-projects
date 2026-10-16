from _shared import MODEL, compatible_client, tracing, workflow


def main():
    with tracing("compatible_surfaces"), compatible_client() as client:

        @workflow(name="openrouter_compatible_surfaces")
        def run(prompt):
            chat = client.chat.completions.create(
                model=MODEL, messages=[{"role": "user", "content": prompt}]
            )
            response = client.responses.create(model=MODEL, input=prompt)
            text = client.completions.create(model=MODEL, prompt=prompt)
            embed = client.embeddings.create(
                model="openai/text-embedding-3-small",
                input=prompt,
                encoding_format="float",
            )
            return {
                "chat": chat.choices[0].message.content,
                "response": response.output_text,
                "text": text.choices[0].text,
                "dimensions": len(embed.data[0].embedding),
            }

        print(run("A bounded fixture prompt."))


if __name__ == "__main__":
    main()
