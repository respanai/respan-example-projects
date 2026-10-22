import os
import subprocess
import sys
import uuid
from pathlib import Path

EXAMPLES = (
    "01_basic_completion.py",
    "02_streaming_completion.py",
    "03_respan_attributes.py",
    "04_tool_calling.py",
    "05_expected_error.py",
    "06_async_completion.py",
    "07_async_streaming.py",
    "08_embeddings_and_tools.py",
    "09_responses.py",
    "10_privacy_and_usage.py",
    "11_large_payloads.py",
)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    env = os.environ.copy()
    env.setdefault("RESPAN_EXAMPLE_RUN_ID", "litellm-" + uuid.uuid4().hex[:10])
    failures = []
    for script_name in EXAMPLES:
        print(f"\n=== {script_name} ===", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, str(base_dir / script_name)],
                cwd=base_dir,
                env=env,
                check=False,
                timeout=240,
            )
            if result.returncode:
                failures.append(script_name)
        except subprocess.TimeoutExpired:
            failures.append(script_name)
    if failures:
        raise SystemExit("LiteLLM examples failed: " + ", ".join(failures))
    print("RESPAN_EXAMPLE_RUN_ID=" + env["RESPAN_EXAMPLE_RUN_ID"])


if __name__ == "__main__":
    main()
