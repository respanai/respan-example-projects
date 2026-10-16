import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

root = Path(__file__).resolve().parent
env = os.environ.copy()
env.setdefault("RESPAN_EXAMPLE_RUN_ID", "marqo-suite-" + uuid4().hex)
if "--export" in sys.argv:
    env["RESPAN_EXAMPLE_EXPORT"] = "1"
for script in sorted(root.glob("[0-9][0-9]_*.py")):
    result = subprocess.run(
        [sys.executable, str(script)], cwd=root, env=env, check=False
    )
    print(f"PROCESS_EXIT script={script.name} code={result.returncode}", flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
