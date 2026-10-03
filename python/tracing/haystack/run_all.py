"""Run all deterministic Haystack scenarios; live gateway calls are opt-in."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live-gateway",
        action="store_true",
        help="Also call the gateway and an existing managed prompt (requires RESPAN_PROMPT_ID).",
    )
    parser.add_argument(
        "--create-prompt",
        action="store_true",
        help="Also create and deploy a managed prompt, then call it through the gateway.",
    )
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    live = {
        "01_setup_respan_gateway.py",
        "41_openai_generator_gateway.py",
        "42_openai_chat_generator_gateway.py",
        "43_prompt_management_gateway.py",
    }
    scripts = [
        script
        for script in sorted(directory.glob("[0-9][0-9]_*.py"))
        if (script.name not in live or args.live_gateway)
        and (
            script.name != "44_prompt_management_extra_body_gateway.py"
            or args.create_prompt
        )
    ]
    scripts.append(directory / "complex_edge_cases.py")
    marker = os.getenv("RESPAN_EXAMPLE_RUN_ID") or "haystack-" + datetime.now(
        UTC
    ).strftime("%Y%m%dT%H%M%SZ")
    environment = {**os.environ, "RESPAN_EXAMPLE_RUN_ID": marker}
    print(f"RESPAN_EXAMPLE_RUN_ID={marker}; scenarios={len(scripts)}", flush=True)
    failures = []
    for script in scripts:
        print(f"\n== running {script.name} ==", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=directory,
                env=environment,
                timeout=120,
                check=False,
            )
            if result.returncode:
                failures.append(f"{script.name}: exit {result.returncode}")
        except subprocess.TimeoutExpired:
            failures.append(f"{script.name}: timeout")
    if failures:
        print("Failures: " + "; ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
