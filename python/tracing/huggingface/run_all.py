"""Run all Hugging Face tracing examples in isolated Python processes."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = [
    "01_text_generation_pipeline.py",
    "02_batch_prompts.py",
    "03_trace_content_disabled.py",
    "04_real_tiny_pipeline.py",
    "05_chat_and_tools.py",
    "06_lazy_iterators.py",
    "07_native_streamer.py",
    "08_native_errors.py",
]


def main() -> None:
    os.environ.setdefault("RESPAN_EXAMPLE_RUN_ID", f"huggingface-{uuid4().hex}")
    for script in SCRIPTS:
        print(f"\n== Running {script} ==", flush=True)
        subprocess.run(
            [sys.executable, str(EXAMPLE_DIR / script)],
            cwd=EXAMPLE_DIR,
            check=True,
        )


if __name__ == "__main__":
    main()
