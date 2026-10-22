"""Complete bounded runner with one exact marker and independent SDK processes."""

import json
import os
import subprocess
import sys
from pathlib import Path

from _shared import example_run_id

EXAMPLES = (
    "01_llm_chat.py",
    "02_streaming_response.py",
    "03_tool_calling.py",
    "04_context_and_error.py",
    "05_live_openai.py",
    "06_content_privacy.py",
    "07_raw_usage.py",
    "08_native_session.py",
)


def run():
    env = dict(os.environ)
    env["RESPAN_EXAMPLE_RUN_ID"] = example_run_id()
    env["PYTHONUNBUFFERED"] = "1"
    failed = []
    for script in EXAMPLES:
        print("\n=== " + script + " marker=" + example_run_id() + " ===", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / script)],
                env=env,
                cwd=Path(__file__).parent,
                timeout=60,
                check=False,
            )
        except subprocess.TimeoutExpired:
            failed.append(script + ": timeout")
            continue
        if result.returncode:
            failed.append(script + ": exit " + str(result.returncode))
    report = {
        "total": len(EXAMPLES),
        "passed": len(EXAMPLES) - len(failed),
        "failed": failed,
        "marker": example_run_id(),
    }
    print(json.dumps(report))
    if os.getenv("LIVEKIT_RUNNER_REPORT"):
        Path(os.environ["LIVEKIT_RUNNER_REPORT"]).write_text(
            json.dumps(report, indent=2)
        )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
