"""Run every Google GenAI tracing example with one audit marker."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

SCRIPTS = (
    "01_generate_content.py",
    "02_stream_content.py",
    "03_async_generate_content.py",
    "04_tool_calling.py",
    "05_embed_content.py",
    "06_async_stream_content.py",
    "07_embedding_error.py",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    env = os.environ.copy()
    env["RESPAN_GOOGLE_GENAI_MODE"] = args.mode
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", f"google-genai-{uuid4().hex[:10]}")
    print(f"RESPAN_EXAMPLE_RUN_ID={env['RESPAN_EXAMPLE_RUN_ID']}", flush=True)
    scripts = SCRIPTS if args.mode == "fixture" else SCRIPTS[:-1]
    for script in scripts:
        subprocess.run([sys.executable, str(directory / script)], env=env, check=True)
    print(
        f"Completed {len(scripts)} Google Gen AI scenarios ({args.mode}).", flush=True
    )


if __name__ == "__main__":
    main()
