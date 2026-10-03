"""Run every Groq example in an isolated process with one audit marker."""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4


def main():
    env = dict(os.environ)
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", "groq-" + uuid4().hex[:12])
    print(f"run_id={env['RESPAN_EXAMPLE_RUN_ID']}", flush=True)
    scripts = sorted(Path(__file__).parent.glob("[0-9][0-9]_*.py"))
    for script in scripts:
        subprocess.run([sys.executable, str(script)], env=env, check=True, timeout=120)
    print(f"completed={len(scripts)}", flush=True)


if __name__ == "__main__":
    main()
