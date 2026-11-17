"""A real LiveKit voice agent, traced by the published Respan SDK.

One scripted phone call to a dental clinic's receptionist agent: a caller asks to
move an appointment, interrupts the agent mid-sentence, and books a new time.

The pipeline is the real LiveKit Agents one: AgentSession with Silero VAD,
speech-to-text (Whisper, on this machine), an LLM (gpt-4o-mini through the Respan
gateway) and text-to-speech (a macOS voice). Only a Respan API key is needed. The only stand-ins are the two ends of
the phone line: the caller's microphone is pre-recorded speech fed in real time,
and the agent's speaker "plays" its audio on a real-time clock, so an
interruption cuts the agent off exactly as it would on a call. No LiveKit server
is needed.

What it writes to ./out:
  otlp_payload.json  the exact JSON bodies the Respan SDK POSTed to /v2/traces
  spans.json         the same spans, flattened: one line per span (name, trace,
                     session, voice timings)
  call.wav           the whole call, both sides, as heard
  call.json          the call's session id and the transcript

Run: python voice_demo.py   (or ./run.sh for the call plus the end-to-end check)
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import wave
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
load_dotenv(HERE / ".env", override=True)

# The framework Python on some Macs ships without a CA bundle; use certifi's.
if not os.environ.get("SSL_CERT_FILE"):
    import certifi

    os.environ["SSL_CERT_FILE"] = certifi.where()

import respan_tracing.exporters.respan as respan_exporter  # noqa: E402
from livekit import rtc  # noqa: E402
from livekit.agents import Agent, AgentSession, TurnHandlingOptions, io  # noqa: E402
from livekit.plugins import openai as lk_openai  # noqa: E402
from livekit.plugins import silero  # noqa: E402
from respan import Respan  # noqa: E402
from respan_instrumentation_livekit import LiveKitInstrumentor  # noqa: E402

from local_speech import MacSayTTS, WhisperSTT, say_to_pcm  # noqa: E402

SAMPLE_RATE = 24000
FRAME_MS = 20
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000
SESSION_ID_ATTRIBUTE = "respan.sessions.session_identifier"

INSTRUCTIONS = (
    "You are the receptionist at Bright Smile Dental, on a phone call. "
    "Keep each reply to one or two spoken sentences, no lists or markdown. "
    "When the caller asks about a day, offer three specific appointment times on "
    "that day with the dentist's name, Dr. Patel, in one longer sentence."
)

# The caller's side of the call. "interrupt" lines are spoken while the agent is
# still talking, this many seconds into its reply.
CALLER_SCRIPT = [
    {"text": "Hi, I need to move my cleaning appointment, it's under Jordan Lee."},
    {"text": "Do you have anything on Thursday afternoon?"},
    {"text": "Sorry, actually Friday morning would be better for me.", "interrupt_after_s": 1.5},
    {"text": "Ten o'clock works, please book it. Thanks!"},
]
EXPECTED_TURNS = len(CALLER_SCRIPT)
EXPECTED_INTERRUPTED_TURN = 2  # 1-based: the agent's reply to line 2 is cut off


class CallRecorder:
    """Both sides of the call on one timeline, written out as call.wav."""

    def __init__(self) -> None:
        self.t0 = time.monotonic()
        self.chunks: list[tuple[float, np.ndarray]] = []

    def add(self, at: float, samples: np.ndarray) -> None:
        self.chunks.append((at - self.t0, samples))

    def write(self, path: Path) -> None:
        if not self.chunks:
            return
        end = max(start + len(s) / SAMPLE_RATE for start, s in self.chunks)
        mix = np.zeros(int(end * SAMPLE_RATE) + 1, dtype=np.int32)
        for start, samples in self.chunks:
            i = int(start * SAMPLE_RATE)
            mix[i : i + len(samples)] += samples.astype(np.int32)
        with wave.open(str(path), "wb") as fh:
            fh.setnchannels(1)
            fh.setsampwidth(2)
            fh.setframerate(SAMPLE_RATE)
            fh.writeframes(np.clip(mix, -32768, 32767).astype(np.int16).tobytes())


class CallerMicrophone(io.AudioInput):
    """The caller's microphone: silence, or the next scripted line, in real time."""

    def __init__(self, recorder: CallRecorder) -> None:
        super().__init__(label="scripted caller")
        self._pending = np.zeros(0, dtype=np.int16)
        self._next_at = time.monotonic()
        self._recorder = recorder
        self.done_speaking = asyncio.Event()

    def say(self, samples: np.ndarray) -> None:
        self._pending = np.concatenate([self._pending, samples])
        self.done_speaking.clear()

    async def __anext__(self) -> rtc.AudioFrame:
        self._next_at += FRAME_MS / 1000
        await asyncio.sleep(max(0.0, self._next_at - time.monotonic()))
        chunk = self._pending[:FRAME_SAMPLES]
        self._pending = self._pending[FRAME_SAMPLES:]
        if len(chunk):
            self._recorder.add(time.monotonic(), chunk)
            if not len(self._pending):
                self.done_speaking.set()
        frame = np.zeros(FRAME_SAMPLES, dtype=np.int16)
        frame[: len(chunk)] = chunk
        return rtc.AudioFrame(data=frame.tobytes(), sample_rate=SAMPLE_RATE,
                              num_channels=1, samples_per_channel=FRAME_SAMPLES)


class PhoneSpeaker(io.AudioOutput):
    """The agent's speaker: audio plays on a real-time clock and stops when cut off."""

    def __init__(self, recorder: CallRecorder) -> None:
        super().__init__(label="phone speaker", next_in_chain=None, sample_rate=SAMPLE_RATE,
                         capabilities=io.AudioOutputCapabilities(pause=False))
        self._recorder = recorder
        self._frames: list[np.ndarray] = []
        self._pushed = 0.0
        self._started = 0.0
        self._interrupted = asyncio.Event()
        self._finishing: asyncio.Task | None = None
        self.interruptions = 0

    async def capture_frame(self, frame: rtc.AudioFrame) -> None:
        await super().capture_frame(frame)
        if self._finishing and not self._finishing.done():
            await self._finishing
        if not self._pushed:
            self._started = time.monotonic()
            self.on_playback_started(created_at=time.time())
        self._frames.append(np.frombuffer(bytes(frame.data), dtype=np.int16))
        self._pushed += frame.duration

    def flush(self) -> None:
        super().flush()
        if self._pushed and not (self._finishing and not self._finishing.done()):
            self._finishing = asyncio.create_task(self._play_out())

    def clear_buffer(self) -> None:
        if self._pushed:
            self._interrupted.set()
            if not (self._finishing and not self._finishing.done()):
                self._finishing = asyncio.create_task(self._play_out())

    async def _play_out(self) -> None:
        remaining = self._started + self._pushed - time.monotonic()
        try:
            await asyncio.wait_for(self._interrupted.wait(), timeout=max(0.0, remaining))
            interrupted = True
        except asyncio.TimeoutError:
            interrupted = False
        played = min(self._pushed, time.monotonic() - self._started) if interrupted else self._pushed
        audio = np.concatenate(self._frames) if self._frames else np.zeros(0, dtype=np.int16)
        self._recorder.add(self._started, audio[: int(played * SAMPLE_RATE)])
        self.interruptions += int(interrupted)
        self._frames, self._pushed = [], 0.0
        self._interrupted.clear()
        self.on_playback_finished(playback_position=played, interrupted=interrupted)


CALLER_VOICE = "Daniel"
AGENT_VOICE = "Samantha"


def caller_voice(text: str) -> np.ndarray:
    """The caller's line as 24 kHz mono PCM (a macOS voice)."""
    return np.frombuffer(say_to_pcm(text, CALLER_VOICE), dtype=np.int16)


def capture_exported_payloads() -> list[dict]:
    """Keep a copy of every OTLP JSON body the SDK sends to /v2/traces."""
    payloads: list[dict] = []
    build = respan_exporter._build_otlp_payload

    def build_and_keep(spans):
        payload = build(spans)
        payloads.append(json.loads(json.dumps(payload, default=str)))
        return payload

    respan_exporter._build_otlp_payload = build_and_keep
    return payloads


def flatten(payloads: list[dict]) -> list[dict]:
    rows = []
    for payload in payloads:
        for resource in payload.get("resourceSpans", []):
            for scope in resource.get("scopeSpans", []):
                for span in scope.get("spans", []):
                    attrs = {a["key"]: next(iter(a.get("value", {}).values()), None)
                             for a in span.get("attributes", [])}
                    rows.append({
                        # The LiveKit span name; Respan's span kind is in "kind".
                        "name": attrs.get("traceloop.entity.name") or span.get("name"),
                        "kind": span.get("name"),
                        "trace_id": span.get("traceId"),
                        "span_id": span.get("spanId"),
                        "parent_span_id": span.get("parentSpanId") or None,
                        "session_id": attrs.get(SESSION_ID_ATTRIBUTE),
                        "voice": {k.split(".voice.", 1)[1]: v for k, v in attrs.items() if ".voice." in k},
                        "attributes": attrs,
                    })
    return rows


async def wait_for(session: AgentSession, state: str, timeout: float = 30.0) -> None:
    if session.agent_state == state:
        return
    reached = asyncio.Event()

    def on_change(ev) -> None:
        if ev.new_state == state:
            reached.set()

    session.on("agent_state_changed", on_change)
    try:
        await asyncio.wait_for(reached.wait(), timeout)
    finally:
        session.off("agent_state_changed", on_change)


async def run_call() -> dict:
    """Run the scripted call; return {session_id, transcript, interruptions}."""
    OUT.mkdir(exist_ok=True)
    payloads = capture_exported_payloads()
    respan = Respan(
        api_key=os.environ["RESPAN_API_KEY"],
        base_url=os.environ.get("RESPAN_BASE_URL", "https://api.respan.ai/api"),
        app_name="livekit-voice-demo",
        instrumentations=[LiveKitInstrumentor()],
    )
    voices = [caller_voice(line["text"]) for line in CALLER_SCRIPT]
    respan_base = os.environ.get("RESPAN_BASE_URL", "https://api.respan.ai/api")

    recorder = CallRecorder()
    microphone = CallerMicrophone(recorder)
    speaker = PhoneSpeaker(recorder)
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=WhisperSTT(),
        llm=lk_openai.LLM(model="gpt-4o-mini", base_url=respan_base,
                          api_key=os.environ["RESPAN_API_KEY"]),
        tts=MacSayTTS(voice=AGENT_VOICE),
        turn_handling=TurnHandlingOptions(
            turn_detection="vad",
            interruption={"enabled": True, "mode": "vad", "min_duration": 0.4,
                          "resume_false_interruption": False},
        ),
    )
    transcript: list[dict] = []

    def on_item(ev) -> None:
        if getattr(ev.item, "type", None) == "message":
            transcript.append({"role": ev.item.role, "text": ev.item.text_content,
                               "interrupted": ev.item.interrupted})

    session.on("conversation_item_added", on_item)
    session.input.audio = microphone
    session.output.audio = speaker
    await session.start(Agent(instructions=INSTRUCTIONS))
    await asyncio.sleep(0.5)

    for i, (line, voice) in enumerate(zip(CALLER_SCRIPT, voices)):
        if "interrupt_after_s" in line:
            # Talk over the agent's reply, this far into it.
            await wait_for(session, "speaking")
            await asyncio.sleep(line["interrupt_after_s"])
        else:
            await wait_for(session, "listening")
        print(f"caller: {line['text']}", flush=True)
        microphone.say(voice)
        await microphone.done_speaking.wait()
        next_line = CALLER_SCRIPT[i + 1] if i + 1 < EXPECTED_TURNS else None
        if next_line is None or "interrupt_after_s" not in next_line:
            # Let the agent answer in full before the caller speaks again.
            await wait_for(session, "speaking")
            await wait_for(session, "listening", timeout=60)
    await asyncio.sleep(1.0)
    await session.aclose()

    respan.shutdown()
    recorder.write(OUT / "call.wav")

    spans = flatten(payloads)
    session_ids = sorted({s["session_id"] for s in spans if s["session_id"]})
    result = {
        "session_id": session_ids[0] if len(session_ids) == 1 else session_ids,
        "transcript": transcript,
        "agent_cut_off": speaker.interruptions,
        "exported_spans": len(spans),
        "export_requests": len(payloads),
    }
    (OUT / "otlp_payload.json").write_text(json.dumps(payloads, indent=2))
    (OUT / "spans.json").write_text(json.dumps(spans, indent=2))
    (OUT / "call.json").write_text(json.dumps(result, indent=2))
    for item in transcript:
        cut = " [cut off]" if item["interrupted"] else ""
        print(f"  {item['role']:>9}: {item['text']}{cut}")
    print(f"session_id={result['session_id']} spans={len(spans)} "
          f"export_requests={len(payloads)} agent_cut_off={speaker.interruptions}", flush=True)
    return result


if __name__ == "__main__":
    asyncio.run(run_call())
