"""Run every mapped Chroma example in the current environment."""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from _shared import SCENARIOS

if __name__ == "__main__":
    env = dict(os.environ)
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", "chroma-local-" + uuid4().hex)
    for scenario in SCENARIOS:
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / (scenario + ".py"))],
            env=env,
            check=True,
        )
