"""Speech that runs on this machine, so the demo needs no speech-provider keys.

  WhisperSTT  LiveKit STT plugin around faster-whisper (base.en, CPU)
  MacSayTTS   LiveKit TTS plugin around macOS's built-in `say` voices

Both are ordinary LiveKit plugins: AgentSession drives them exactly as it would a
hosted provider (Silero VAD segments the caller's speech for the STT), so the
turn timings LiveKit records, and the Respan SDK exports, are the real pipeline's.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import wave

import numpy as np
from faster_whisper import WhisperModel
from livekit import rtc
from livekit.agents import stt, tts, utils
from livekit.agents.language import LanguageCode
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, APIConnectOptions, NotGivenOr

WHISPER_SAMPLE_RATE = 16000
SAY_SAMPLE_RATE = 24000


class WhisperSTT(stt.STT):
    def __init__(self, *, model: str = "base.en") -> None:
        super().__init__(capabilities=stt.STTCapabilities(streaming=False, interim_results=False))
        self._model_name = model
        self._whisper = WhisperModel(model, device="cpu", compute_type="int8")

    @property
    def model(self) -> str:
        return self._model_name

    @property
    def provider(self) -> str:
        return "faster-whisper"

    async def _recognize_impl(self, buffer: utils.AudioBuffer, *,
                              language: NotGivenOr[str] = NOT_GIVEN,
                              conn_options: APIConnectOptions) -> stt.SpeechEvent:
        frame = rtc.combine_audio_frames(buffer)
        resampler = rtc.AudioResampler(input_rate=frame.sample_rate, output_rate=WHISPER_SAMPLE_RATE,
                                       num_channels=frame.num_channels)
        pcm = b"".join(bytes(f.data) for f in [*resampler.push(frame), *resampler.flush()])
        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

        def transcribe() -> str:
            segments, _ = self._whisper.transcribe(audio, language="en", beam_size=1)
            return " ".join(s.text.strip() for s in segments).strip()

        text = await asyncio.to_thread(transcribe)
        return stt.SpeechEvent(type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                               alternatives=[stt.SpeechData(language=LanguageCode("en"), text=text)])


def say_to_pcm(text: str, voice: str) -> bytes:
    """`say` rendered to 24 kHz mono 16-bit PCM."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "speech.wav")
        os.spawnvp(os.P_WAIT, "say", ["say", "-v", voice, "-o", path,
                                      "--file-format=WAVE", f"--data-format=LEI16@{SAY_SAMPLE_RATE}", text])
        with wave.open(path, "rb") as fh:
            return fh.readframes(fh.getnframes())


class MacSayTTS(tts.TTS):
    def __init__(self, *, voice: str = "Samantha") -> None:
        super().__init__(capabilities=tts.TTSCapabilities(streaming=False),
                         sample_rate=SAY_SAMPLE_RATE, num_channels=1)
        self._voice = voice

    @property
    def model(self) -> str:
        return self._voice

    @property
    def provider(self) -> str:
        return "macos-say"

    def synthesize(self, text: str, *,
                   conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS) -> tts.ChunkedStream:
        return _SayStream(tts=self, input_text=text, conn_options=conn_options)


class _SayStream(tts.ChunkedStream):
    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        pcm = await asyncio.to_thread(say_to_pcm, self._input_text, self._tts._voice)
        output_emitter.initialize(request_id=utils.shortuuid(), sample_rate=SAY_SAMPLE_RATE,
                                  num_channels=1, mime_type="audio/pcm")
        output_emitter.push(pcm)
        output_emitter.flush()
