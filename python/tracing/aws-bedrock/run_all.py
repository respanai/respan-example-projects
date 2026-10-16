from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path


def run():
    here = Path(__file__).resolve().parent
    os.environ.setdefault("RESPAN_EXAMPLE_RUN_ID", "bedrock-" + uuid.uuid4().hex)
    failures = []
    examples = sorted(here.glob("[0-9][0-9]_*.py"))
    for example in examples:
        result = subprocess.run([sys.executable, str(example)], check=False)
        if result.returncode:
            failures.append(example.name)
    if failures:
        raise SystemExit("Bedrock example failures: " + ", ".join(failures))
    print(
        f"Complete suite: {len(examples)} scripts; native capability skips are printed; optional AWS live call is separately gated"
    )


if __name__ == "__main__":
    run()
