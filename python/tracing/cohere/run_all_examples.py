from __future__ import annotations

import subprocess
import sys
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
EXAMPLES = [
    "01_chat.py",
    "02_streaming_chat.py",
    "03_embed_rerank.py",
    "04_async_tools_and_error.py",
    "05_async_streaming.py",
]


def main() -> None:
    for example in EXAMPLES:
        print(f"\n=== {example} ===")
        subprocess.run(
            [sys.executable, str(EXAMPLE_DIR / example)],
            check=True,
        )


if __name__ == "__main__":
    main()
