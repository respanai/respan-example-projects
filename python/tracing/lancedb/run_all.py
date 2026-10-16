import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

root = Path(__file__).parent
env = dict(os.environ)
env.setdefault("RESPAN_EXAMPLE_RUN_ID", f"lancedb-suite-{uuid4().hex}")
for script in sorted(root.glob("[0-9][0-9]_*.py")):
    result = subprocess.run([sys.executable, str(script)], env=env, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)
