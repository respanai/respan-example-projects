"""Compatibility alias for the workflow/API Dify tracing example."""

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).with_name("04_workflow_and_api.py")), run_name="__main__"
)
