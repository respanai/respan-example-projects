"""Compatibility alias for the streaming Dify chat example."""

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).with_name("02_chat_streaming.py")), run_name="__main__"
)
