"""Actual released native Responses.parse typed return values."""

import asyncio
from importlib.metadata import version

from _shared import (
    async_client,
    create_respan,
    finish_respan,
    provider_config,
    sync_client,
    workflow,
)
from pydantic import BaseModel


class City(BaseModel):
    city: str


def main():
    if version("openlit") < "1.45.0":
        print("SKIP: native Responses.parse instrumentation requires OpenLIT1.45")
        return
    telemetry = create_respan("parsed-models")

    @workflow(name="parsed_models")
    def run():
        client = sync_client(config)
        try:
            result = client.responses.parse(
                model=config.model, input="typed-city", text_format=City
            )
            assert (
                isinstance(result.output_parsed, City)
                and result.output_parsed.city == "Paris"
            )
        finally:
            client.close()

        async def call():
            client = async_client(config)
            try:
                result = await client.responses.parse(
                    model=config.model, input="typed-city", text_format=City
                )
                assert (
                    isinstance(result.output_parsed, City)
                    and result.output_parsed.city == "Paris"
                )
            finally:
                await client.close()

        asyncio.run(call())
        return {"city": "Paris", "native_parsed_model": True}

    try:
        with provider_config(force_mock=True) as config:
            print(run())
    finally:
        finish_respan(telemetry)


if __name__ == "__main__":
    main()
