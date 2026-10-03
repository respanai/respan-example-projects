"""Run every committed Semantic Kernel tracing example."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = (
    "01_kernel_function.py",
    "02_chat_completion.py",
    "03_plugin_tool_call.py",
    "04_function_failure.py",
    "05_agent_methods.py",
    "06_embeddings.py",
    "07_streaming.py",
    "08_content_policy.py",
    "09_capture_opt_out.py",
)


def main() -> None:
    root = Path(__file__).resolve().parent
    env = os.environ.copy()
    env.setdefault(
        "RESPAN_EXAMPLE_RUN_ID",
        datetime.now(timezone.utc).strftime("otel2-semantic-kernel-%Y%m%dT%H%M%SZ"),
    )
    print(f"marker={env['RESPAN_EXAMPLE_RUN_ID']} scripts={len(SCRIPTS)}", flush=True)
    failures: list[str] = []
    for script in SCRIPTS:
        try:
            result = subprocess.run(
                [sys.executable, str(root / script)],
                check=False,
                cwd=root,
                env=env,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{script}: timeout")
            continue
        if result.returncode:
            failures.append(f"{script}: exit {result.returncode}")
    if failures:
        raise SystemExit("; ".join(failures))
    print(f"completed={len(SCRIPTS)} marker={env['RESPAN_EXAMPLE_RUN_ID']}", flush=True)


if __name__ == "__main__":
    main()
