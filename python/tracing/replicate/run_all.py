import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

SCRIPTS = tuple(p.name for p in sorted(Path(__file__).parent.glob("[0-9][0-9]_*.py")))


def main():
    root = Path(__file__).resolve().parent
    env = {
        **os.environ,
        "RESPAN_EXAMPLE_RUN_ID": os.getenv("RESPAN_EXAMPLE_RUN_ID")
        or "replicate-" + uuid4().hex,
    }
    failed = []
    for script in SCRIPTS:
        print(script, flush=True)
        try:
            result = subprocess.run(
                [sys.executable, str(root / script)],
                cwd=root,
                env=env,
                check=False,
                timeout=60,
            )
            if result.returncode:
                failed.append(script)
        except subprocess.TimeoutExpired:
            failed.append(script + " timeout")
    if failed:
        raise SystemExit("; ".join(failed))


if __name__ == "__main__":
    main()
