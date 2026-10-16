from __future__ import annotations

import asyncio

from _shared import (
    async_client,
    create_respan,
    example_scope,
    finish_respan,
    provider_config,
    sync_client,
    workflow,
)

SCENARIO = "sync-async-embedding"


def run_workflow(config) -> dict[str, object]:
    client = sync_client(config)

    @workflow(name="openlit_sync_async_embedding_workflow")
    def traced_workflow(
        sync_prompt: str,
        async_prompt: str,
        embedding_input: str,
    ) -> dict[str, object]:
        response = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": sync_prompt}],
        )
        embedding = client.embeddings.create(
            model=config.embedding_model,
            input=[embedding_input],
        )

        async def async_call() -> str:
            async_openai = async_client(config)
            try:
                async_response = await async_openai.responses.create(
                    model=config.model,
                    input=async_prompt,
                )
                return async_response.output_text
            finally:
                await async_openai.close()

        return {
            "sync": response.choices[0].message.content or "",
            "async": asyncio.run(async_call()),
            "embedding_dimensions": len(embedding.data[0].embedding),
        }

    try:
        return traced_workflow(
            sync_prompt="Reply with one short sentence.",
            async_prompt="Reply with one short async sentence.",
            embedding_input="bounded OpenLIT embedding example",
        )
    finally:
        client.close()


def main() -> None:
    respan = create_respan(SCENARIO)
    try:
        with provider_config() as config, example_scope(SCENARIO):
            result = run_workflow(config)
            print(f"{SCENARIO}: {result}", flush=True)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
