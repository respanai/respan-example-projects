from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = (
    "01_chat_completion.py",
    "02_async_chat_completion.py",
    "03_streaming_chat.py",
    "04_tool_calling.py",
    "05_expected_error.py",
    "06_live_portkey.py",
    "07_embeddings.py",
    "08_responses.py",
    "09_structured_chat.py",
    "10_prompt_and_text.py",
    "11_private_content.py",
    "12_stream_error.py",
    "13_tools_and_stream.py",
)
DEFAULT_TIMEOUT_SECONDS = 120.0


def main() -> None:
    run_marker = os.getenv("RESPAN_EXAMPLE_RUN_ID", "").strip() or (
        "portkey-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    timeout = float(
        os.getenv("RESPAN_EXAMPLE_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
    )
    env = os.environ.copy()
    env["RESPAN_EXAMPLE_RUN_ID"] = run_marker
    failures: list[str] = []
    for script in SCRIPTS:
        print(f"\n### Running {script}", flush=True)
        try:
            completed = subprocess.run(
                [sys.executable, str(EXAMPLE_DIR / script)],
                check=False,
                env=env,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{script}: timed out after {timeout:g}s")
            continue
        if completed.returncode:
            failures.append(f"{script}: exited {completed.returncode}")
    if failures:
        raise SystemExit("Portkey example failures:\n- " + "\n- ".join(failures))
    print(f"\nCompleted Portkey examples: RESPAN_EXAMPLE_RUN_ID={run_marker}")


if __name__ == "__main__":
    main()
