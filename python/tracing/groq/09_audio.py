"""Transcription, translation and speech, including lazy binary consumption."""

import os

from _shared import make_async_client, make_client, run_example


async def scenario():
    if os.getenv("RESPAN_GROQ_FIXTURE") != "1":
        raise RuntimeError(
            "This example uses synthetic audio; set RESPAN_GROQ_FIXTURE=1"
        )
    upload = ("synthetic.wav", b"synthetic upload", "audio/wav")
    with make_client() as client:
        client.audio.transcriptions.create(model="whisper-large-v3", file=upload)
        client.audio.translations.create(model="whisper-large-v3", file=upload)
        response = client.audio.speech.create(
            model="playai-tts", input="synthetic speech", voice="fixture"
        )
        response.read()
        response.close()
    async with make_async_client() as client:
        await client.audio.transcriptions.create(model="whisper-large-v3", file=upload)
        async with client.audio.translations.with_streaming_response.create(
            model="whisper-large-v3", file=upload
        ) as response:
            await response.parse()
        async with client.audio.speech.with_streaming_response.create(
            model="playai-tts", input="synthetic speech", voice="fixture"
        ) as response:
            data = b"".join([chunk async for chunk in response.iter_bytes()])
    return {"audio_bytes": len(data)}


if __name__ == "__main__":
    run_example("audio", scenario)
