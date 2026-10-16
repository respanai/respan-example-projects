"""Compatibility alias for the Respan context and file-upload example."""

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).with_name("05_respan_context_and_files.py")), run_name="__main__"
)
