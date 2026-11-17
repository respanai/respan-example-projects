"""A local OpenAI-compatible speech server, for the TypeScript demo.

The Node agent uses LiveKit's stock OpenAI STT and TTS plugins pointed at this
server, so its speech runs on this machine like the Python demo's:

  POST /v1/audio/transcriptions   (multipart WAV) -> {"text": ...}   faster-whisper
  POST /v1/audio/speech           {"input", "voice"} -> 24 kHz PCM    macOS `say`

Run: .venv/bin/python speech_server.py [port]   (default 8765; listens on 127.0.0.1)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from email.parser import BytesParser
from email.policy import HTTP
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from faster_whisper import WhisperModel

from local_speech import say_to_pcm

MAC_VOICES = {"Samantha", "Daniel", "Karen", "Moira", "Tessa", "Fred"}
DEFAULT_VOICE = "Samantha"
WHISPER = WhisperModel("base.en", device="cpu", compute_type="int8")


def multipart_file(content_type: str, body: bytes) -> bytes:
    message = BytesParser(policy=HTTP).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode() + body)
    for part in message.iter_parts():
        if part.get_param("name", header="content-disposition") == "file":
            return part.get_payload(decode=True)
    raise ValueError("no file part")


class Handler(BaseHTTPRequestHandler):
    def _reply(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 (http.server's name)
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            if self.path.endswith("/audio/transcriptions"):
                audio = multipart_file(self.headers["Content-Type"], body)
                with tempfile.NamedTemporaryFile(suffix=".wav") as fh:
                    fh.write(audio)
                    fh.flush()
                    segments, _ = WHISPER.transcribe(fh.name, language="en", beam_size=1)
                    text = " ".join(s.text.strip() for s in segments).strip()
                self._reply(200, json.dumps({"text": text}).encode(), "application/json")
            elif self.path.endswith("/audio/speech"):
                request = json.loads(body)
                voice = request.get("voice") if request.get("voice") in MAC_VOICES else DEFAULT_VOICE
                self._reply(200, say_to_pcm(request["input"], voice), "audio/pcm")
            else:
                self._reply(404, b'{"error": "not found"}', "application/json")
        except Exception as error:  # a demo server: report, never crash
            self._reply(500, json.dumps({"error": str(error)}).encode(), "application/json")

    def log_message(self, *_args) -> None:
        return


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("SPEECH_PORT", 8765))
    print(f"speech server on http://127.0.0.1:{port}/v1", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
