from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

EXAMPLE_SCRIPTS = (
    "01_chat_provider.py",
    "02_tool_call.py",
    "03_embedding.py",
    "04_expected_failure.py",
    "05_streaming_privacy.py",
    "06_content_veto.py",
    "07_native_openai.py",
    "08_multimodal_usage.py",
    "09_native_decorators.py",
)
EXAMPLE_TIMEOUT_SECONDS = 120


def resolved_run_id() -> str:
    return os.getenv("RESPAN_EXAMPLE_RUN_ID") or (
        f"openinference-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )


def main() -> int:
    directory = Path(__file__).resolve().parent
    environment = os.environ.copy()
    environment["RESPAN_EXAMPLE_RUN_ID"] = resolved_run_id()
    failures: list[tuple[str, int | str]] = []

    print(f"example_run_id={environment['RESPAN_EXAMPLE_RUN_ID']}", flush=True)
    for script in EXAMPLE_SCRIPTS:
        print(f"running={script}", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, str(directory / script)],
                cwd=directory,
                env=environment,
                check=False,
                timeout=EXAMPLE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            print(
                f"finished={script} timeout={EXAMPLE_TIMEOUT_SECONDS}s",
                flush=True,
            )
            failures.append((script, "timeout"))
            continue
        print(f"finished={script} exit={result.returncode}", flush=True)
        if result.returncode:
            failures.append((script, result.returncode))

    if failures:
        print(f"failures={failures}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
