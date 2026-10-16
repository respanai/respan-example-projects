"""The installed observation command returns neutral permission JSON."""

import json
import os
import subprocess
import sys


def main():
    env = os.environ.copy()
    env["TRACE_TO_RESPAN"] = "off"
    for name, expected in [
        ("beforeSubmitPrompt", {"continue": True}),
        ("preToolUse", {"permission": "allow"}),
        ("beforeReadFile", {"permission": "allow"}),
        ("beforeMCPExecution", {"permission": "allow"}),
        ("subagentStart", {"permission": "allow"}),
    ]:
        result = subprocess.run(
            [sys.executable, "-m", "respan_instrumentation_cursor_sdk"],
            input=json.dumps(
                {"hook_event_name": name, "prompt": "Controlled hook input"}
            ),
            text=True,
            capture_output=True,
            env=env,
            timeout=20,
            check=True,
        )
        assert json.loads(result.stdout) == expected
    print("5 installed CLI protocol checks passed; explicit trace-export opt-out")


if __name__ == "__main__":
    main()
