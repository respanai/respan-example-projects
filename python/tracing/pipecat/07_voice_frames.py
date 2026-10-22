import asyncio

from _pipeline import run
from _shared import attributes, create_respan, finish_respan, marker, print_result
from _voice_service import STT, TTS
from respan import workflow


async def main():
    run_id = marker()
    sdk = create_respan("voice-frames", run_id)

    @workflow(name="pipecat_voice_frames")
    async def scenario():
        stt, _ = await run(service=STT())
        tts, _ = await run(service=TTS())
        return {
            "transcription_frames": sum(
                type(f).__name__ == "TranscriptionFrame" for f in stt.frames
            ),
            "speech_text_frames": sum(
                type(f).__name__ == "TTSTextFrame" for f in tts.frames
            ),
            "live_audio_inference": False,
        }

    try:
        with attributes("voice-frames", run_id):
            result = await scenario()
        print_result("voice-frames", result, run_id)
    finally:
        finish_respan(sdk)


if __name__ == "__main__":
    asyncio.run(main())
