from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

EXAMPLE_DIR = Path(__file__).resolve().parent
EXAMPLES = (
    "01_chat_completion.py",
    "02_multi_turn_chat.py",
    "03_async_chat_completion.py",
    "04_sync_streaming.py",
    "05_async_streaming.py",
    "06_tool_calling.py",
    "07_expected_provider_failure.py",
    "08_expected_application_failure.py",
    "09_structured_output.py",
    "10_agent_completions.py",
)


def main() -> None:
    parent_marker = os.getenv("RESPAN_EXAMPLE_RUN_ID") or (
        f"mistralai-{uuid4().hex[:12]}"
    )
    child_environment = os.environ.copy()
    child_environment["RESPAN_EXAMPLE_RUN_ID"] = parent_marker
    print(f"example_run_id={parent_marker}", flush=True)

    failures = []
    for filename in EXAMPLES:
        print(f"\n=== {filename} ===", flush=True)
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_DIR / filename)],
            cwd=EXAMPLE_DIR,
            env=child_environment,
            check=False,
        )
        if result.returncode:
            failures.append((filename, result.returncode))

    if failures:
        rendered = ", ".join(f"{name} ({code})" for name, code in failures)
        raise SystemExit(f"Mistral example failures: {rendered}")


if __name__ == "__main__":
    main()
