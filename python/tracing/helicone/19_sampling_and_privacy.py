"""Run Helicone policy examples in independent OpenTelemetry processes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

from _policy_runtime import MODES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, help="Run only one policy case")
    args = parser.parse_args()
    run_id = (
        os.getenv("RESPAN_EXAMPLE_RUN_ID") or f"helicone-policy-{uuid.uuid4().hex[:12]}"
    )
    results = []
    for mode in [args.mode] if args.mode else MODES:
        child_env = dict(os.environ)
        child_env["RESPAN_EXAMPLE_RUN_ID"] = run_id
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("_policy_runtime.py")), mode],
            env=child_env,
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            # The child never prints credentials or request headers. Keep its
            # assertion evidence visible without dumping native request bodies.
            sys.stderr.write(result.stdout + result.stderr)
            raise SystemExit(result.returncode)
        reports = [line for line in result.stdout.splitlines() if line.startswith("{")]
        if not reports:
            raise RuntimeError(f"No policy report returned for {mode}")
        results.append(json.loads(reports[-1]))
    print(
        json.dumps(
            {
                "example": "helicone-sampling-and-privacy",
                "run_id": run_id,
                "policy_cases": len(results),
                "exported_spans": sum(item["exported_spans"] for item in results),
                "native_spans": sum(item["native_spans"] for item in results),
                "native_http_posts": sum(item["native_http_posts"] for item in results),
                "results": results,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
