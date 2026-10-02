from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
SCRIPTS = (
    "01_llm_log_request.py",
    "02_builder_streaming.py",
    "03_builder_error.py",
    "04_tool_log.py",
    "05_vector_db_log.py",
    "06_data_log.py",
    "07_anthropic_direct_log.py",
    "08_log_request_error.py",
    "10_text_completion.py",
    "11_embedding.py",
    "12_capture_content_false.py",
    "13_delayed_builder_context.py",
    "14_log_request_stream.py",
    "15_anthropic_stream.py",
    "16_google_and_nested_failure.py",
    "17_builder_response.py",
    "18_builder_cancelled.py",
)
LIVE_SCRIPT = "09_live_helicone.py"
DEFAULT_TIMEOUT_SECONDS = 120.0


def main() -> None:
    run_marker = os.getenv("RESPAN_EXAMPLE_RUN_ID", "").strip() or (
        "helicone-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
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
        raise SystemExit("Helicone example failures:\n- " + "\n- ".join(failures))
    print(f"\nCompleted Helicone examples: RESPAN_EXAMPLE_RUN_ID={run_marker}")


if __name__ == "__main__":
    main()
