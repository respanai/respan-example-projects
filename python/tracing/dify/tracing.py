"""Compatibility alias for the blocking Dify chat tracing example."""

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).with_name("01_chat_blocking.py")), run_name="__main__"
)
