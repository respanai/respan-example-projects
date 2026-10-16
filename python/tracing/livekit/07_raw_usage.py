"""Absent and invalid raw provider usage is omitted before SDK coercion."""

import asyncio

from _shared import Tracing, chat_context, native_job, provider_model


async def main():
    tracing = Tracing("raw-usage")
    try:
        with native_job():
            for usage in [
                False,
                {
                    "prompt_tokens": False,
                    "completion_tokens": False,
                    "total_tokens": False,
                },
            ]:
                model, client = provider_model(usage=usage)
                try:
                    assert (
                        await model.chat(chat_ctx=chat_context()).collect()
                    ).text == "actual provider fixture"
                finally:
                    await client.close()
                    await model.aclose()
        spans = [
            s
            for s in tracing.exporter.get_finished_spans()
            if s.attributes.get("respan.entity.log_type") == "chat"
        ]
        assert len(spans) == 2 and all(
            not any("usage" in k for k in s.attributes) for s in spans
        )
        print("native values preserved; absent/boolean raw counts omitted")
    finally:
        tracing.finish()


if __name__ == "__main__":
    asyncio.run(main())
