import asyncio

from _native import Native
from _shared import Runtime
from replicate.helpers import FileOutput


async def main():
    r = Runtime("file_output")
    n = Native("https://replicate.delivery/controlled/output/file")
    try:
        with r.workflow():
            # Explicit option keeps this example compatible with native SDK1.0.0 and1.0.7 defaults.
            result = n.client.run(
                "owner/model", input={"prompt": "Controlled file"}, use_file_output=True
            )
            assert type(result) is FileOutput and result.read() == b"native"
            result = await n.client.async_run(
                "owner/model",
                input={"prompt": "Controlled async file"},
                use_file_output=True,
            )
            assert type(result) is FileOutput and await result.aread() == b"native"
    finally:
        await n.client._async_client.aclose()
        n.close()
        r.close()


asyncio.run(main())
