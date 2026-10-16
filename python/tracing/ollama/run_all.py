"""Run every Ollama tracing example with one exact batch marker."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = (
    "01_chat.py",
    "02_stream_generate.py",
    "03_tool_calling.py",
    "04_embeddings.py",
    "05_expected_error.py",
    "06_async.py",
    "07_content_policy.py",
    "08_optional_live.py",
)


def main() -> None:
    env = os.environ.copy()
    run_id = env.get("RESPAN_EXAMPLE_RUN_ID") or datetime.now(timezone.utc).strftime(
        "ollama-suite-%Y%m%dT%H%M%SZ"
    )
    env["RESPAN_EXAMPLE_RUN_ID"] = run_id
    print(f"RESPAN_EXAMPLE_RUN_ID={run_id}", flush=True)

    failures: list[tuple[str, int]] = []
    for script in SCRIPTS:
        print(f"\n=== {script} ===", flush=True)
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_DIR / script)],
            cwd=EXAMPLE_DIR,
            env=env,
            check=False,
        )
        print(f"PROCESS_EXIT script={script} code={result.returncode}", flush=True)
        if result.returncode:
            failures.append((script, result.returncode))

    if failures:
        rendered = ", ".join(f"{name} ({code})" for name, code in failures)
        raise SystemExit(f"Ollama example failures: {rendered}")


if __name__ == "__main__":
    main()
