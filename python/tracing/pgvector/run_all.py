"""Run every numbered native example in a separate interpreter."""

import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).parent
for script in sorted(root.glob("[0-9][0-9]_*.py")):
    result = subprocess.run(
        [sys.executable, str(script)], cwd=root, env=os.environ.copy(), check=False
    )
    if result.returncode:
        raise SystemExit(result.returncode)
